from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from math import sqrt
from typing import Any, Dict, List

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

logger = logging.getLogger(__name__)

FEATURE_KEYS = [
    "price_fairness",
    "availability_confidence",
    "trust_score",
    "demand_pressure",
    "negotiation_probability",
]

DEFAULT_WEIGHTS = {
    "price_weight": 0.28,
    "availability_weight": 0.24,
    "trust_weight": 0.22,
    "demand_weight": 0.14,
    "negotiation_weight": 0.12,
}


class DecisionModelService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db

    async def _ensure_control(self) -> Dict[str, Any]:
        control = await self.db.decision_model_config.find_one({"_id": "decision_model_control"})
        if control:
            return control
        now = datetime.now(timezone.utc)
        control = {
            "_id": "decision_model_control",
            "active_version": 1,
            "created_at": now,
            "updated_at": now,
        }
        await self.db.decision_model_config.insert_one(control)
        return control

    async def ensure_active_model(self) -> Dict[str, Any]:
        control = await self._ensure_control()
        active_version = int(control.get("active_version", 1))
        active = await self.db.decision_model_config.find_one({"risk_version": {"$exists": False}, "model_version": active_version})
        if active:
            if not active.get("active_flag", False):
                await self.db.decision_model_config.update_one({"_id": active["_id"]}, {"$set": {"active_flag": True}})
            return active

        now = datetime.now(timezone.utc)
        default_doc = {
            "_id": ObjectId(),
            "model_version": 1,
            "weights": DEFAULT_WEIGHTS,
            "performance_metrics": {
                "booking_prediction_accuracy": 0.0,
                "dispute_prediction_accuracy": 0.0,
                "average_score_error": 0.0,
                "sample_size": 0,
            },
            "active_flag": True,
            "frozen": False,
            "created_at": now,
            "last_calibration_date": now,
        }
        await self.db.decision_model_config.insert_one(default_doc)
        await self.db.decision_model_config.update_one(
            {"_id": "decision_model_control"},
            {"$set": {"active_version": 1, "updated_at": now}},
            upsert=True,
        )
        return default_doc

    async def get_active_model(self) -> Dict[str, Any]:
        control = await self._ensure_control()
        active_version = int(control.get("active_version", 1))
        model = await self.db.decision_model_config.find_one({"model_version": active_version, "risk_version": {"$exists": False}})
        if model:
            return model
        return await self.ensure_active_model()

    async def rollback_to_version(self, target_version: int) -> Dict[str, Any]:
        model = await self.db.decision_model_config.find_one({"model_version": target_version, "risk_version": {"$exists": False}})
        if not model:
            return {"status": "error", "reason": "target_version_not_found"}
        now = datetime.now(timezone.utc)
        await self.db.decision_model_config.update_many(
            {"model_version": {"$exists": True}, "risk_version": {"$exists": False}},
            {"$set": {"active_flag": False}},
        )
        await self.db.decision_model_config.update_one({"_id": model["_id"]}, {"$set": {"active_flag": True}})
        await self.db.decision_model_config.update_one(
            {"_id": "decision_model_control"},
            {"$set": {"active_version": int(target_version), "updated_at": now}},
            upsert=True,
        )
        return {"status": "ok", "active_version": int(target_version)}

    @staticmethod
    def _corr(xs: List[float], ys: List[float]) -> float:
        n = min(len(xs), len(ys))
        if n < 50:
            return 0.0
        x_mean = sum(xs[:n]) / n
        y_mean = sum(ys[:n]) / n
        cov = sum((xs[i] - x_mean) * (ys[i] - y_mean) for i in range(n))
        x_var = sum((xs[i] - x_mean) ** 2 for i in range(n))
        y_var = sum((ys[i] - y_mean) ** 2 for i in range(n))
        if x_var <= 0 or y_var <= 0:
            return 0.0
        return cov / (sqrt(x_var) * sqrt(y_var))

    @staticmethod
    def _normalize(weights: Dict[str, float]) -> Dict[str, float]:
        total = max(1e-9, sum(weights.values()))
        return {k: v / total for k, v in weights.items()}

    def _bounded_shift(self, current: Dict[str, float], target: Dict[str, float]) -> Dict[str, float]:
        shifted: Dict[str, float] = {}
        for k, current_w in current.items():
            ratio = (target.get(k, current_w) / max(1e-9, current_w)) - 1.0
            capped_ratio = max(-0.10, min(0.10, ratio))
            shifted[k] = current_w * (1.0 + capped_ratio)
        return self._normalize(shifted)

    def _weight_changes(self, old: Dict[str, float], new: Dict[str, float]) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for key, old_val in old.items():
            out[key] = round(((new.get(key, old_val) - old_val) / max(1e-9, old_val)), 6)
        return out

    def _max_weight_delta(self, old: Dict[str, float], new: Dict[str, float]) -> float:
        deltas = self._weight_changes(old, new)
        return max(abs(v) for v in deltas.values()) if deltas else 0.0

    def _evaluate_booking_accuracy(self, rows: List[Dict[str, Any]], weights: Dict[str, float]) -> float:
        correct = 0
        for row in rows:
            feat = row.get("predicted_features", {})
            score = (
                float(feat.get("price_fairness", 0.0)) * float(weights.get("price_weight", 0.28))
                + float(feat.get("availability_confidence", 0.0)) * float(weights.get("availability_weight", 0.24))
                + float(feat.get("trust_score", 0.0)) * float(weights.get("trust_weight", 0.22))
                + float(feat.get("demand_pressure", 0.0)) * float(weights.get("demand_weight", 0.14))
                + float(feat.get("negotiation_probability", 0.0)) * float(weights.get("negotiation_weight", 0.12))
            ) * 100.0
            pred = score >= 70.0
            if pred == bool(row.get("actual_booking_result")):
                correct += 1
        return round(correct / max(1, len(rows)), 4)

    async def _acquire_lock(self, owner_id: str, lease_seconds: int = 900) -> bool:
        now = datetime.now(timezone.utc)
        lease_until = now + timedelta(seconds=lease_seconds)
        lock = await self.db.calibration_locks.find_one_and_update(
            {
                "_id": "decision_model_calibration",
                "$or": [
                    {"lease_expires_at": {"$lte": now}},
                    {"lease_expires_at": {"$exists": False}},
                    {"owner_id": owner_id},
                ],
            },
            {
                "$set": {
                    "owner_id": owner_id,
                    "lease_expires_at": lease_until,
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return bool(lock and lock.get("owner_id") == owner_id)

    async def _release_lock(self, owner_id: str) -> None:
        now = datetime.now(timezone.utc)
        await self.db.calibration_locks.update_one(
            {"_id": "decision_model_calibration", "owner_id": owner_id},
            {"$set": {"lease_expires_at": now, "updated_at": now}},
        )

    async def _write_audit(
        self,
        *,
        model_version_from: int,
        model_version_to: int | None,
        previous_accuracy: float,
        new_accuracy: float,
        weight_changes: Dict[str, float],
        aborted_flag: bool,
        reason: str,
    ) -> None:
        await self.db.calibration_audit_logs.insert_one(
            {
                "_id": ObjectId(),
                "model_version_from": model_version_from,
                "model_version_to": model_version_to,
                "previous_accuracy": previous_accuracy,
                "new_accuracy": new_accuracy,
                "weight_changes": weight_changes,
                "aborted_flag": aborted_flag,
                "reason": reason,
                "created_at": datetime.now(timezone.utc),
            }
        )

    async def calibrate_model(
        self,
        sample_size: int = 10000,
        *,
        manual_override: bool = False,
        triggered_by: str = "system",
    ) -> Dict[str, Any]:
        owner_id = f"{triggered_by}:{uuid.uuid4().hex}"
        locked = await self._acquire_lock(owner_id)
        if not locked:
            return {"status": "skipped", "reason": "calibration_locked"}

        active_model = await self.get_active_model()
        current_version = int(active_model.get("model_version", 1))
        current_weights = active_model.get("weights", DEFAULT_WEIGHTS)
        try:
            if bool(active_model.get("frozen", False)) and not manual_override:
                await self._write_audit(
                    model_version_from=current_version,
                    model_version_to=None,
                    previous_accuracy=0.0,
                    new_accuracy=0.0,
                    weight_changes={},
                    aborted_flag=True,
                    reason="model_frozen",
                )
                return {"status": "skipped", "reason": "model_frozen", "model_version": current_version}

            rows = await self.db.decision_outcomes.find(
                {"actual_completion_status": "completed"},
                projection={"predicted_features": 1, "actual_booking_result": 1, "actual_dispute_flag": 1},
                sort=[("created_at", -1)],
                limit=sample_size,
                batch_size=1000,
            ).to_list(length=sample_size)
            row_count = len(rows)
            if row_count < 1000:
                await self._write_audit(
                    model_version_from=current_version,
                    model_version_to=None,
                    previous_accuracy=0.0,
                    new_accuracy=0.0,
                    weight_changes={},
                    aborted_flag=True,
                    reason="insufficient_completed_outcomes",
                )
                return {"status": "skipped", "reason": "insufficient_completed_outcomes", "sample_size": row_count}

            feature_vectors: Dict[str, List[float]] = {k: [] for k in FEATURE_KEYS}
            success_target: List[float] = []
            for row in rows:
                pred = row.get("predicted_features", {})
                booking_result = 1.0 if row.get("actual_booking_result") else 0.0
                dispute_penalty = 0.35 if row.get("actual_dispute_flag") else 0.0
                success_target.append(max(0.0, min(1.0, booking_result - dispute_penalty)))
                for f in FEATURE_KEYS:
                    feature_vectors[f].append(float(pred.get(f, 0.0)))

            corr_map = {
                "price_weight": abs(self._corr(feature_vectors["price_fairness"], success_target)),
                "availability_weight": abs(self._corr(feature_vectors["availability_confidence"], success_target)),
                "trust_weight": abs(self._corr(feature_vectors["trust_score"], success_target)),
                "demand_weight": abs(self._corr(feature_vectors["demand_pressure"], success_target)),
                "negotiation_weight": abs(self._corr(feature_vectors["negotiation_probability"], success_target)),
            }
            corr_map = {k: max(0.01, v) for k, v in corr_map.items()}
            target_weights = self._normalize(corr_map)
            bounded_weights = self._bounded_shift(current_weights, target_weights)
            weight_changes = self._weight_changes(current_weights, bounded_weights)

            max_delta = self._max_weight_delta(current_weights, bounded_weights)
            if max_delta > 0.25:
                await self._write_audit(
                    model_version_from=current_version,
                    model_version_to=None,
                    previous_accuracy=0.0,
                    new_accuracy=0.0,
                    weight_changes=weight_changes,
                    aborted_flag=True,
                    reason="weight_delta_exceeded_cap",
                )
                return {"status": "aborted", "reason": "weight_delta_exceeded_cap", "max_weight_delta": max_delta}

            previous_accuracy = self._evaluate_booking_accuracy(rows, current_weights)
            new_accuracy = self._evaluate_booking_accuracy(rows, bounded_weights)
            if max_delta < 0.0001 and abs(new_accuracy - previous_accuracy) < 0.001:
                await self._write_audit(
                    model_version_from=current_version,
                    model_version_to=None,
                    previous_accuracy=previous_accuracy,
                    new_accuracy=new_accuracy,
                    weight_changes=weight_changes,
                    aborted_flag=True,
                    reason="no_material_change",
                )
                return {"status": "skipped", "reason": "no_material_change"}
            if new_accuracy < previous_accuracy - 0.05:
                await self._write_audit(
                    model_version_from=current_version,
                    model_version_to=None,
                    previous_accuracy=previous_accuracy,
                    new_accuracy=new_accuracy,
                    weight_changes=weight_changes,
                    aborted_flag=True,
                    reason="booking_accuracy_regression_gt_5pct",
                )
                return {
                    "status": "aborted",
                    "reason": "booking_accuracy_regression_gt_5pct",
                    "previous_accuracy": previous_accuracy,
                    "new_accuracy": new_accuracy,
                }

            now = datetime.now(timezone.utc)
            next_version = current_version + 1
            new_model = {
                "_id": ObjectId(),
                "model_version": next_version,
                "weights": bounded_weights,
                "performance_metrics": {
                    "booking_prediction_accuracy_estimate": new_accuracy,
                    "previous_booking_prediction_accuracy_estimate": previous_accuracy,
                    "calibration_sample_size": row_count,
                    "feature_correlation": corr_map,
                },
                "active_flag": True,
                "frozen": bool(active_model.get("frozen", False)),
                "created_at": now,
                "last_calibration_date": now,
            }

            try:
                async with await self.db.client.start_session() as session:
                    async with session.start_transaction():
                        await self.db.decision_model_config.update_many(
                            {"model_version": {"$exists": True}, "risk_version": {"$exists": False}},
                            {"$set": {"active_flag": False}},
                            session=session,
                        )
                        await self.db.decision_model_config.insert_one(new_model, session=session)
                        await self.db.decision_model_config.update_one(
                            {"_id": "decision_model_control"},
                            {"$set": {"active_version": next_version, "updated_at": now}},
                            upsert=True,
                            session=session,
                        )
            except Exception as tx_err:
                # Standalone MongoDB nodes (used in tests/dev) do not support transactions.
                # Fall back to sequential non-transactional writes.
                _standalone_errs = ("Transaction numbers are only allowed on a replica set member",
                                    "transaction", "not supported")
                err_msg = str(tx_err).lower()
                if any(e.lower() in err_msg for e in _standalone_errs):
                    logger.warning("MongoDB transaction unavailable (%s); falling back to sequential writes", type(tx_err).__name__)
                    await self.db.decision_model_config.update_many(
                        {"model_version": {"$exists": True}, "risk_version": {"$exists": False}},
                        {"$set": {"active_flag": False}},
                    )
                    await self.db.decision_model_config.insert_one(dict(new_model))
                    await self.db.decision_model_config.update_one(
                        {"_id": "decision_model_control"},
                        {"$set": {"active_version": next_version, "updated_at": now}},
                        upsert=True,
                    )
                else:
                    raise

            await self._write_audit(
                model_version_from=current_version,
                model_version_to=next_version,
                previous_accuracy=previous_accuracy,
                new_accuracy=new_accuracy,
                weight_changes=weight_changes,
                aborted_flag=False,
                reason="calibration_applied",
            )
            logger.info("model_calibrated version=%s sample=%s by=%s", next_version, row_count, triggered_by)
            return {
                "status": "ok",
                "model_version_from": current_version,
                "model_version_to": next_version,
                "previous_accuracy": previous_accuracy,
                "new_accuracy": new_accuracy,
                "weight_changes": weight_changes,
                "sample_size": row_count,
            }
        except Exception as exc:
            await self._write_audit(
                model_version_from=current_version,
                model_version_to=None,
                previous_accuracy=0.0,
                new_accuracy=0.0,
                weight_changes={},
                aborted_flag=True,
                reason=f"exception:{type(exc).__name__}",
            )
            raise
        finally:
            await self._release_lock(owner_id)

    async def get_model_performance(self, model_version: int | None = None) -> Dict[str, Any]:
        active = await self.get_active_model()
        target_version = model_version if model_version is not None else int(active.get("model_version", 1))
        cursor = self.db.decision_outcomes.find(
            {"model_version": target_version},
            projection={
                "actual_booking_result": 1,
                "actual_dispute_flag": 1,
                "predicted_booking_result": 1,
                "predicted_dispute_flag": 1,
                "accuracy_metrics.score_error": 1,
            },
            sort=[("created_at", -1)],
            limit=5000,
        )
        rows = await cursor.to_list(length=5000)
        failure_count = await self.db.calibration_audit_logs.count_documents(
            {"model_version_from": target_version, "aborted_flag": True}
        )
        last_aborted = await self.db.calibration_audit_logs.find_one(
            {"model_version_from": target_version, "aborted_flag": True},
            sort=[("created_at", -1)],
            projection={"reason": 1},
        )
        recent_success = await self.db.calibration_audit_logs.find(
            {"aborted_flag": False},
            sort=[("created_at", -1)],
            projection={"weight_changes": 1},
            limit=5,
        ).to_list(length=5)
        change_values: List[float] = []
        for row in recent_success:
            for delta in row.get("weight_changes", {}).values():
                change_values.append(abs(float(delta)))
        avg_delta = sum(change_values) / max(1, len(change_values))
        weight_stability_index = round(max(0.0, min(1.0, 1.0 - (avg_delta / 0.10))), 4)
        created_at = active.get("created_at", datetime.now(timezone.utc))
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        model_age_days = round((datetime.now(timezone.utc) - created_at).total_seconds() / 86400.0, 3)

        if not rows:
            return {
                "current_model_version": target_version,
                "booking_prediction_accuracy": 0.0,
                "dispute_prediction_accuracy": 0.0,
                "average_score_error": 0.0,
                "last_calibration_date": active.get("last_calibration_date", active.get("created_at", datetime.now(timezone.utc))),
                "calibration_failure_count": failure_count,
                "last_aborted_reason": (last_aborted or {}).get("reason"),
                "weight_stability_index": weight_stability_index,
                "model_age_days": model_age_days,
            }

        booking_correct = 0
        dispute_correct = 0
        score_errors: List[float] = []
        for row in rows:
            if bool(row.get("predicted_booking_result")) == bool(row.get("actual_booking_result")):
                booking_correct += 1
            if bool(row.get("predicted_dispute_flag")) == bool(row.get("actual_dispute_flag")):
                dispute_correct += 1
            score_errors.append(float(row.get("accuracy_metrics", {}).get("score_error", 0.0)))

        return {
            "current_model_version": target_version,
            "booking_prediction_accuracy": round(booking_correct / len(rows), 4),
            "dispute_prediction_accuracy": round(dispute_correct / len(rows), 4),
            "average_score_error": round(sum(score_errors) / max(1, len(score_errors)), 4),
            "last_calibration_date": active.get("last_calibration_date", active.get("created_at", datetime.now(timezone.utc))),
            "calibration_failure_count": failure_count,
            "last_aborted_reason": (last_aborted or {}).get("reason"),
            "weight_stability_index": weight_stability_index,
            "model_age_days": model_age_days,
        }

    async def run_calibration_loop(self, interval_seconds: int = 3600) -> None:
        while True:
            try:
                active = await self.get_active_model()
                last = active.get("last_calibration_date", active.get("created_at", datetime.now(timezone.utc)))
                if isinstance(last, str):
                    last = datetime.fromisoformat(last)
                if datetime.now(timezone.utc) - last >= timedelta(days=7):
                    await self.calibrate_model(manual_override=False, triggered_by="auto")
            except Exception as exc:
                logger.exception("model_calibration_loop_failure error=%s", str(exc))
            await asyncio.sleep(interval_seconds)
