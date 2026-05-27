from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.decision_model_service import DecisionModelService


class FeatureMonitorService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db

    @staticmethod
    def _mean(values: List[float]) -> float:
        return sum(values) / max(1, len(values))

    @staticmethod
    def _std(values: List[float], mean_value: float) -> float:
        if len(values) < 2:
            return 0.0
        variance = sum((x - mean_value) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(max(0.0, variance))

    async def _feature_values(self, feature_name: str, limit: int = 1000) -> List[float]:
        if feature_name == "dispute_risk_score":
            rows = await self.db.booking_risk_snapshots.find(
                {},
                projection={"dispute_risk_score": 1},
                sort=[("created_at", -1)],
                limit=limit,
            ).to_list(length=limit)
            return [float(r.get("dispute_risk_score", 0.0)) for r in rows]
        if feature_name == "risk_adjusted_score":
            rows = await self.db.decision_scores.find(
                {},
                projection={"risk_adjusted_score": 1},
                sort=[("created_at", -1)],
                limit=limit,
            ).to_list(length=limit)
            return [float(r.get("risk_adjusted_score", r.get("score", 0.0))) for r in rows]
        if feature_name == "demand_pressure":
            rows = await self.db.market_signals.find(
                {},
                projection={"demand_pressure": 1},
                sort=[("created_at", -1)],
                limit=limit,
            ).to_list(length=limit)
            return [float(r.get("demand_pressure", 0.0)) for r in rows]
        if feature_name == "city_surge_index":
            rows = await self.db.market_signals.find(
                {},
                projection={"city_surge_index": 1},
                sort=[("created_at", -1)],
                limit=limit,
            ).to_list(length=limit)
            return [float(r.get("city_surge_index", 0.0)) for r in rows]
        return []

    async def evaluate_feature_drift(self) -> Dict[str, Any]:
        feature_names = ["dispute_risk_score", "risk_adjusted_score", "demand_pressure", "city_surge_index"]
        now = datetime.now(timezone.utc)
        events = []
        stats: Dict[str, Any] = {}
        for feature in feature_names:
            values = await self._feature_values(feature, limit=1000)
            if len(values) < 100:
                stats[feature] = {"insufficient_data": True, "sample_size": len(values)}
                continue
            recent = values[:50]
            baseline = values[50:]
            baseline_mean = self._mean(baseline)
            baseline_std = self._std(baseline, baseline_mean)
            current_mean = self._mean(recent)
            z_score = 0.0 if baseline_std <= 1e-9 else (current_mean - baseline_mean) / baseline_std
            stats[feature] = {
                "rolling_mean": round(current_mean, 6),
                "baseline_mean": round(baseline_mean, 6),
                "baseline_std": round(baseline_std, 6),
                "z_score": round(z_score, 6),
            }
            if abs(z_score) > 3.0:
                event = {
                    "_id": ObjectId(),
                    "feature_name": feature,
                    "rolling_mean": current_mean,
                    "baseline_mean": baseline_mean,
                    "baseline_std": baseline_std,
                    "z_score": z_score,
                    "created_at": now,
                }
                events.append(event)
        if events:
            await self.db.feature_drift_alerts.insert_many(events, ordered=False)
        return {"evaluated_at": now, "drift_events_created": len(events), "stats": stats}

    async def get_drift_status(self) -> Dict[str, Any]:
        await self.evaluate_feature_drift()
        recent_alerts = await self.db.feature_drift_alerts.find(
            {},
            sort=[("created_at", -1)],
            limit=100,
        ).to_list(length=100)
        count_24h = await self.db.feature_drift_alerts.count_documents({"created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=1)}})
        return {
            "drift_alert_count_24h": count_24h,
            "latest_alerts": recent_alerts,
        }

    @staticmethod
    def _distribution(values: List[float]) -> Dict[str, int]:
        bins = {"0_20": 0, "20_40": 0, "40_60": 0, "60_80": 0, "80_100": 0}
        for v in values:
            if v < 20:
                bins["0_20"] += 1
            elif v < 40:
                bins["20_40"] += 1
            elif v < 60:
                bins["40_60"] += 1
            elif v < 80:
                bins["60_80"] += 1
            else:
                bins["80_100"] += 1
        return bins

    async def get_ai_health(self, decision_model_service: DecisionModelService) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=7)
        risk_rows = await self.db.booking_risk_snapshots.find(
            {"created_at": {"$gte": since}},
            projection={"dispute_risk_score": 1},
            limit=10000,
        ).to_list(length=10000)
        decision_rows = await self.db.decision_scores.find(
            {"created_at": {"$gte": since}},
            projection={"risk_adjusted_score": 1, "score": 1},
            limit=10000,
        ).to_list(length=10000)
        drift_alert_count = await self.db.feature_drift_alerts.count_documents({"created_at": {"$gte": since}})
        perf = await decision_model_service.get_model_performance()

        risk_values = [float(r.get("dispute_risk_score", 0.0)) for r in risk_rows]
        decision_values = [float(r.get("risk_adjusted_score", r.get("score", 0.0))) for r in decision_rows]

        calibration_stability_index = float(perf.get("weight_stability_index", 0.0))
        accuracy = float(perf.get("booking_prediction_accuracy", 0.0))
        drift_penalty = min(0.4, drift_alert_count / 1000.0)
        model_confidence_score = max(
            0.0,
            min(1.0, (accuracy * 0.55) + (calibration_stability_index * 0.35) + (0.10 - drift_penalty)),
        )
        return {
            "current_model_version": perf.get("current_model_version"),
            "risk_score_distribution_last_7d": self._distribution(risk_values),
            "decision_score_distribution_last_7d": self._distribution(decision_values),
            "drift_alert_count": drift_alert_count,
            "calibration_stability_index": round(calibration_stability_index, 4),
            "model_confidence_score": round(model_confidence_score, 4),
        }

