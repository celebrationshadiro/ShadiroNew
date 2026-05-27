from __future__ import annotations

import logging
import uuid
from hashlib import sha256
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.services.ai_control_service import AIControlService

logger = logging.getLogger(__name__)


DEFAULT_RISK_MODEL = {
    "risk_version": 1,
    "weights": {
        "vendor_dispute_ratio_weight": 0.22,
        "milestone_delay_rate_weight": 0.18,
        "cancellation_rate_weight": 0.18,
        "negotiation_aggressiveness_weight": 0.14,
        "trust_score_weight": 0.16,
        "historical_price_deviation_weight": 0.12,
    },
    "adjustment": {
        "dispute_risk_weight": 0.18,
        "demand_urgency_weight": 0.14,
    },
}


class RiskService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.ai_control_service = AIControlService(db)

    async def _ensure_risk_control(self) -> Dict[str, Any]:
        control = await self.db.risk_model_config.find_one({"_id": "risk_model_control"})
        if control:
            return control
        now = datetime.now(timezone.utc)
        control = {
            "_id": "risk_model_control",
            "active_version": 1,
            "canary_version": None,
            "canary_traffic_percentage": 0,
            "shadow_version": None,
            "created_at": now,
            "updated_at": now,
        }
        await self.db.risk_model_config.insert_one(control)
        return control

    async def _ensure_default_model(self) -> Dict[str, Any]:
        model = await self.db.risk_model_config.find_one({"risk_version": 1})
        if model:
            return model
        now = datetime.now(timezone.utc)
        default_model = {
            "_id": ObjectId(),
            **DEFAULT_RISK_MODEL,
            "active_flag": True,
            "created_at": now,
        }
        await self.db.risk_model_config.insert_one(default_model)
        return default_model

    async def get_active_risk_model(self) -> Dict[str, Any]:
        control = await self._ensure_risk_control()
        await self._ensure_default_model()
        active_version = int(control.get("active_version", 1))
        model = await self.db.risk_model_config.find_one({"risk_version": active_version, "active_flag": True})
        if model:
            return model
        return await self._ensure_default_model()

    @staticmethod
    def _is_canary_traffic(request_id: str, percent: int) -> bool:
        if percent <= 0:
            return False
        digest = sha256(request_id.encode("utf-8")).hexdigest()
        bucket = int(digest[:8], 16) % 100
        return bucket < percent

    async def _select_model(self, request_id: str) -> tuple[Dict[str, Any], bool]:
        control = await self._ensure_risk_control()
        await self._ensure_default_model()
        active_version = int(control.get("active_version", 1))
        canary_version = control.get("canary_version")
        canary_percent = int(control.get("canary_traffic_percentage", 0))
        is_canary = canary_version is not None and self._is_canary_traffic(request_id, canary_percent)
        selected_version = int(canary_version) if is_canary else active_version
        model = await self.db.risk_model_config.find_one({"risk_version": selected_version, "active_flag": True})
        if model:
            return model, is_canary
        fallback = await self.get_active_risk_model()
        return fallback, False

    async def rollback_to_version(self, target_version: int) -> Dict[str, Any]:
        model = await self.db.risk_model_config.find_one({"risk_version": int(target_version)})
        if not model:
            return {"status": "error", "reason": "target_version_not_found"}
        now = datetime.now(timezone.utc)
        await self.db.risk_model_config.update_many(
            {"risk_version": {"$exists": True}},
            {"$set": {"active_flag": False}},
        )
        await self.db.risk_model_config.update_one(
            {"_id": model["_id"]},
            {"$set": {"active_flag": True}},
        )
        await self.db.risk_model_config.update_one(
            {"_id": "risk_model_control"},
            {
                "$set": {
                    "active_version": int(target_version),
                    "updated_at": now,
                }
            },
            upsert=True,
        )
        return {"status": "ok", "active_version": int(target_version)}

    async def _historical_price_deviation(self, vendor_id) -> float:
        since = datetime.now(timezone.utc) - timedelta(days=180)
        pipeline = [
            {"$match": {"vendor_id": vendor_id, "created_at": {"$gte": since}}},
            {"$group": {"_id": None, "avg_error": {"$avg": "$accuracy_metrics.price_fairness_error"}}},
        ]
        rows = await self.db.decision_outcomes.aggregate(pipeline, allowDiskUse=True).to_list(length=1)
        return float(rows[0].get("avg_error", 0.0)) if rows else 0.0

    async def _acquire_rebalance_lock(self, owner_id: str, lease_seconds: int = 120) -> bool:
        now = datetime.now(timezone.utc)
        lock = await self.db.risk_rebalance_locks.find_one_and_update(
            {
                "_id": "risk_weight_rebalance",
                "$or": [
                    {"lease_expires_at": {"$lte": now}},
                    {"lease_expires_at": {"$exists": False}},
                    {"owner_id": owner_id},
                ],
            },
            {
                "$set": {
                    "owner_id": owner_id,
                    "lease_expires_at": now + timedelta(seconds=lease_seconds),
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return bool(lock and lock.get("owner_id") == owner_id)

    async def _release_rebalance_lock(self, owner_id: str) -> None:
        now = datetime.now(timezone.utc)
        await self.db.risk_rebalance_locks.update_one(
            {"_id": "risk_weight_rebalance", "owner_id": owner_id},
            {"$set": {"lease_expires_at": now, "updated_at": now}},
        )

    @staticmethod
    def _normalize(weights: Dict[str, float]) -> Dict[str, float]:
        total = max(1e-9, sum(weights.values()))
        return {k: max(0.0, v / total) for k, v in weights.items()}

    async def _validate_financial_controls(self) -> None:
        cfg = await self.ai_control_service.get_financial_control()
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=1)
        pipeline = [
            {"$match": {"created_at": {"$gte": since}}},
            {"$group": {"_id": None, "risk_exposure": {"$sum": "$dispute_risk_score"}}},
        ]
        rows = await self.db.booking_risk_snapshots.aggregate(pipeline, allowDiskUse=True).to_list(length=1)
        risk_exposure = float(rows[0].get("risk_exposure", 0.0)) if rows else 0.0
        dispute_rows = await self.db.decision_outcomes.find(
            {"created_at": {"$gte": since}},
            projection={"actual_dispute_flag": 1},
            limit=10000,
        ).to_list(length=10000)
        dispute_rate = sum(1 for r in dispute_rows if bool(r.get("actual_dispute_flag", False))) / max(1, len(dispute_rows))
        if risk_exposure > float(cfg.get("max_daily_risk_exposure", 100000.0)) or dispute_rate > float(cfg.get("max_dispute_rate", 0.15)):
            if bool(cfg.get("auto_freeze_enabled", True)):
                await self.ai_control_service.set_freeze(risk=True)
            raise RuntimeError("financial_safety_threshold_breached")

    async def _get_booking_accuracy_window(self, start: datetime, end: datetime) -> float:
        rows = await self.db.decision_outcomes.find(
            {"created_at": {"$gte": start, "$lt": end}},
            projection={"predicted_booking_result": 1, "actual_booking_result": 1},
            limit=5000,
        ).to_list(length=5000)
        if not rows:
            return 0.0
        correct = 0
        for row in rows:
            if bool(row.get("predicted_booking_result")) == bool(row.get("actual_booking_result")):
                correct += 1
        return correct / max(1, len(rows))

    async def maybe_auto_rebalance_weights(self) -> Dict[str, Any]:
        if await self.ai_control_service.is_frozen("risk"):
            return {"status": "skipped", "reason": "risk_model_frozen"}
        owner_id = f"rebalance:{uuid.uuid4().hex}"
        if not await self._acquire_rebalance_lock(owner_id):
            return {"status": "aborted", "reason": "concurrent_update_detected"}
        try:
            latest = await self.db.risk_weight_audit_logs.find_one({}, sort=[("created_at", -1)])
            if latest and latest.get("created_at") and datetime.now(timezone.utc) - latest["created_at"] < timedelta(hours=12):
                return {"status": "skipped", "reason": "recent_rebalance_exists"}

            now = datetime.now(timezone.utc)
            dispute_rows = await self.db.decision_outcomes.aggregate(
                [
                    {"$match": {"created_at": {"$gte": now - timedelta(days=30)}}},
                    {"$group": {"_id": None, "disputes": {"$sum": {"$cond": ["$actual_dispute_flag", 1, 0]}}, "count": {"$sum": 1}}},
                ],
                allowDiskUse=True,
            ).to_list(length=1)
            dispute_rate = 0.0
            if dispute_rows:
                dispute_rate = float(dispute_rows[0].get("disputes", 0)) / max(1.0, float(dispute_rows[0].get("count", 1)))

            current_accuracy = await self._get_booking_accuracy_window(now - timedelta(days=14), now)
            previous_accuracy = await self._get_booking_accuracy_window(now - timedelta(days=28), now - timedelta(days=14))
            accuracy_drop = previous_accuracy - current_accuracy
            if dispute_rate <= 0.15 or accuracy_drop <= 0.05:
                return {
                    "status": "skipped",
                    "reason": "threshold_not_met",
                    "dispute_rate": round(dispute_rate, 4),
                    "accuracy_drop": round(accuracy_drop, 4),
                }

            model = await self.get_active_risk_model()
            control = await self._ensure_risk_control()
            old_weights = dict(model.get("weights", DEFAULT_RISK_MODEL["weights"]))
            new_weights = dict(old_weights)
            key = "negotiation_aggressiveness_weight"
            new_weights[key] = max(0.0, old_weights.get(key, 0.14) * 0.9)
            new_weights = self._normalize(new_weights)
            next_version = int(model.get("risk_version", 1)) + 1
            now = datetime.now(timezone.utc)

            new_model = {
                "_id": ObjectId(),
                "risk_version": next_version,
                "weights": new_weights,
                "adjustment": model.get("adjustment", DEFAULT_RISK_MODEL["adjustment"]),
                "active_flag": True,
                "created_at": now,
            }
            await self.db.risk_model_config.insert_one(new_model)
            await self.db.risk_model_config.update_one(
                {"_id": "risk_model_control"},
                {
                    "$set": {
                        "canary_version": next_version,
                        "canary_traffic_percentage": int(control.get("canary_traffic_percentage", 10) or 10),
                        "updated_at": now,
                    }
                },
            )
            await self.db.risk_weight_audit_logs.insert_one(
                {
                    "_id": ObjectId(),
                    "from_risk_version": int(model.get("risk_version", 1)),
                    "to_risk_version": next_version,
                    "dispute_rate": round(dispute_rate, 6),
                    "booking_accuracy_previous": round(previous_accuracy, 6),
                    "booking_accuracy_current": round(current_accuracy, 6),
                    "accuracy_drop": round(accuracy_drop, 6),
                    "weight_changes": {
                        k: round((new_weights[k] - old_weights.get(k, 0.0)), 8)
                        for k in new_weights
                    },
                    "reason": "auto_rebalance_triggered",
                    "created_at": now,
                }
            )
            return {"status": "ok", "new_risk_version": next_version}
        finally:
            await self._release_rebalance_lock(owner_id)

    async def predict_dispute_risk(
        self,
        *,
        request_id: str,
        booking_id: str,
        event_id: str,
        vendor_id,
        category: str,
        city: str,
        trust_score: float,
        negotiation_probability: float,
        quoted_price: float,
        demand_pressure: float,
    ) -> Dict[str, Any]:
        if await self.ai_control_service.is_frozen("risk"):
            return {
                "dispute_risk_score": 0.0,
                "risk_version": 1,
                "risk_adjustment_weights": DEFAULT_RISK_MODEL["adjustment"],
                "signals": {},
                "is_canary": False,
                "fallback_used": True,
            }
        try:
            await self._validate_financial_controls()
        except Exception:
            return {
                "dispute_risk_score": 0.0,
                "risk_version": 1,
                "risk_adjustment_weights": DEFAULT_RISK_MODEL["adjustment"],
                "signals": {},
                "is_canary": False,
                "fallback_used": True,
            }
        model, is_canary = await self._select_model(request_id=request_id)
        control = await self._ensure_risk_control()
        risk_version = int(model.get("risk_version", 1))
        w = model.get("weights", DEFAULT_RISK_MODEL["weights"])

        analytics = await self.db.vendor_analytics.find_one(
            {"vendor_id": vendor_id},
            sort=[("day", -1)],
            projection={
                "dispute_ratio": 1,
                "milestone_delay_rate": 1,
                "cancellation_rate": 1,
                "counter_offer_frequency": 1,
                "avg_discount_given": 1,
            },
        ) or {}

        dispute_ratio = max(0.0, min(1.0, float(analytics.get("dispute_ratio", 0.0))))
        milestone_delay_rate = max(0.0, min(1.0, float(analytics.get("milestone_delay_rate", 0.0))))
        cancellation_rate = max(0.0, min(1.0, float(analytics.get("cancellation_rate", 0.0))))
        counter_offer_frequency = max(0.0, min(1.0, float(analytics.get("counter_offer_frequency", 0.0))))
        avg_discount_given = max(0.0, min(100.0, float(analytics.get("avg_discount_given", 0.0))))
        negotiation_aggressiveness = max(
            0.0,
            min(1.0, (counter_offer_frequency * 0.7) + ((avg_discount_given / 100.0) * 0.3)),
        )
        trust_risk = max(0.0, min(1.0, 1.0 - (trust_score / 100.0)))
        historical_price_deviation = max(0.0, min(1.0, (await self._historical_price_deviation(vendor_id))))

        raw = (
            dispute_ratio * float(w.get("vendor_dispute_ratio_weight", 0.22))
            + milestone_delay_rate * float(w.get("milestone_delay_rate_weight", 0.18))
            + cancellation_rate * float(w.get("cancellation_rate_weight", 0.18))
            + negotiation_aggressiveness * float(w.get("negotiation_aggressiveness_weight", 0.14))
            + trust_risk * float(w.get("trust_score_weight", 0.16))
            + historical_price_deviation * float(w.get("historical_price_deviation_weight", 0.12))
        )
        market_pressure_adjustment = max(0.0, min(0.1, demand_pressure * 0.05))
        probability = max(0.0, min(1.0, raw + market_pressure_adjustment - (negotiation_probability * 0.03)))
        dispute_risk_score = round(probability * 100.0, 2)

        now = datetime.now(timezone.utc)
        snapshot = {
            "_id": ObjectId(),
            "booking_id": booking_id,
            "event_id": event_id,
            "vendor_id": vendor_id,
            "category": category,
            "city": city,
            "quoted_price": quoted_price,
            "trust_score": round(trust_score, 2),
            "negotiation_probability": round(negotiation_probability, 4),
            "signals": {
                "vendor_dispute_ratio": dispute_ratio,
                "milestone_delay_rate": milestone_delay_rate,
                "cancellation_rate": cancellation_rate,
                "negotiation_aggressiveness": round(negotiation_aggressiveness, 4),
                "historical_booking_price_deviation": round(historical_price_deviation, 4),
            },
            "risk_version": risk_version,
            "dispute_risk_score": dispute_risk_score,
            "created_at": now,
        }
        await self.db.booking_risk_snapshots.insert_one(snapshot)
        shadow_version = control.get("shadow_version")
        if shadow_version is not None:
            shadow_model = await self.db.risk_model_config.find_one({"risk_version": int(shadow_version)})
            if shadow_model:
                sw = shadow_model.get("weights", DEFAULT_RISK_MODEL["weights"])
                shadow_raw = (
                    dispute_ratio * float(sw.get("vendor_dispute_ratio_weight", 0.22))
                    + milestone_delay_rate * float(sw.get("milestone_delay_rate_weight", 0.18))
                    + cancellation_rate * float(sw.get("cancellation_rate_weight", 0.18))
                    + negotiation_aggressiveness * float(sw.get("negotiation_aggressiveness_weight", 0.14))
                    + trust_risk * float(sw.get("trust_score_weight", 0.16))
                    + historical_price_deviation * float(sw.get("historical_price_deviation_weight", 0.12))
                )
                shadow_probability = max(0.0, min(1.0, shadow_raw + market_pressure_adjustment - (negotiation_probability * 0.03)))
                await self.db.shadow_model_logs.insert_one(
                    {
                        "_id": ObjectId(),
                        "request_id": request_id,
                        "booking_id": booking_id,
                        "active_risk_version": risk_version,
                        "shadow_version": int(shadow_version),
                        "active_dispute_risk_score": dispute_risk_score,
                        "shadow_dispute_risk_score": round(shadow_probability * 100.0, 2),
                        "timestamp": now,
                    }
                )
        await self.maybe_auto_rebalance_weights()
        logger.info("dispute_risk_scored booking_id=%s risk=%.2f", booking_id, dispute_risk_score)
        return {
            "dispute_risk_score": dispute_risk_score,
            "risk_version": risk_version,
            "risk_adjustment_weights": model.get("adjustment", DEFAULT_RISK_MODEL["adjustment"]),
            "signals": snapshot["signals"],
            "is_canary": is_canary,
            "fallback_used": False,
        }
