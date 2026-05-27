from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.profit_monitor_service import ProfitMonitorService
from app.services.vendor_analytics_service import VendorAnalyticsService

logger = logging.getLogger(__name__)


class DecisionOutcomeService:
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        vendor_analytics_service: VendorAnalyticsService,
        profit_monitor_service: ProfitMonitorService,
    ) -> None:
        self.db = db
        self.vendor_analytics_service = vendor_analytics_service
        self.profit_monitor_service = profit_monitor_service

    @staticmethod
    def _target_score(actual_booking_result: bool, dispute_flag: bool) -> float:
        if actual_booking_result and not dispute_flag:
            return 100.0
        if actual_booking_result and dispute_flag:
            return 60.0
        return 20.0

    async def record_booking_outcome(self, booking_id, category: str = "unknown") -> Dict[str, Any]:
        booking = await self.db.bookings.find_one({"_id": booking_id})
        if not booking:
            return {"status": "skipped", "reason": "booking_not_found"}

        decision = await self.db.decision_scores.find_one(
            {"event_id": booking["event_id"], "vendor_id": booking["vendor_id"]},
            sort=[("created_at", -1)],
        )
        if not decision:
            decision = booking.get("decision_snapshot")
        if not decision:
            return {"status": "skipped", "reason": "decision_missing"}

        dispute_exists = await self.db.escrow_transactions.find_one(
            {"booking_id": booking_id, "tx_type": "dispute", "status": {"$in": ["open", "resolved", "succeeded"]}},
            projection={"_id": 1},
        )
        release_pipeline = [
            {"$match": {"booking_id": booking_id, "tx_type": "release", "status": "succeeded"}},
            {"$group": {"_id": None, "final_price": {"$sum": "$amount"}}},
        ]
        release_sum = await self.db.escrow_transactions.aggregate(release_pipeline).to_list(length=1)
        actual_final_price = float(release_sum[0]["final_price"]) if release_sum else float(booking.get("total_amount", 0.0))

        actual_booking_result = booking.get("status") in {"completed", "in_progress"}
        actual_completion_status = booking.get("status", "unknown")
        actual_dispute_flag = bool(dispute_exists)
        model_version = int(decision.get("model_version", 1))

        predicted_score = float(decision.get("score", 0.0))
        comp = decision.get("components", {})
        predicted_negotiation_probability = float(comp.get("negotiation_probability", 0.0)) / 100.0
        predicted_trust_score = float(comp.get("trust_score", 0.0)) / 100.0
        predicted_price_fairness = float(comp.get("price_fairness", 0.0)) / 100.0
        quoted_price = float(decision.get("quoted_price", booking.get("total_amount", 1.0)))
        actual_price_fairness = max(0.0, min(1.0, 1.0 - abs(actual_final_price - quoted_price) / max(1.0, quoted_price)))

        predicted_booking_result = bool(decision.get("recommendation") == "book_now" or predicted_score >= 70.0)
        predicted_dispute_flag = bool(predicted_trust_score < 0.55)
        target_score = self._target_score(actual_booking_result, actual_dispute_flag)

        accuracy_metrics = {
            "score_error": round(abs(predicted_score - target_score), 4),
            "negotiation_probability_error": round(abs(predicted_negotiation_probability - (1.0 if actual_booking_result else 0.0)), 4),
            "trust_score_error": round(abs(predicted_trust_score - (0.3 if actual_dispute_flag else 0.9)), 4),
            "price_fairness_error": round(abs(predicted_price_fairness - actual_price_fairness), 4),
            "booking_prediction_correct": predicted_booking_result == actual_booking_result,
            "dispute_prediction_correct": predicted_dispute_flag == actual_dispute_flag,
        }

        now = datetime.now(timezone.utc)
        outcome_doc = {
            "decision_id": decision.get("_id"),
            "booking_id": booking_id,
            "event_id": booking["event_id"],
            "vendor_id": booking["vendor_id"],
            "actual_booking_result": actual_booking_result,
            "actual_completion_status": actual_completion_status,
            "actual_dispute_flag": actual_dispute_flag,
            "actual_final_price": round(actual_final_price, 2),
            "model_version": model_version,
            "predicted_booking_result": predicted_booking_result,
            "predicted_dispute_flag": predicted_dispute_flag,
            "predicted_features": {
                "price_fairness": predicted_price_fairness,
                "availability_confidence": float(comp.get("availability_confidence", 0.0)) / 100.0,
                "trust_score": predicted_trust_score,
                "demand_pressure": float(comp.get("demand_pressure", 0.0)) / 100.0,
                "negotiation_probability": predicted_negotiation_probability,
            },
            "accuracy_metrics": accuracy_metrics,
            "updated_at": now,
        }
        await self.db.decision_outcomes.update_one(
            {"booking_id": booking_id},
            {"$set": outcome_doc, "$setOnInsert": {"_id": ObjectId(), "created_at": now}},
            upsert=True,
        )
        dispute_penalty = 0.25 if actual_dispute_flag else 0.0
        revenue_impact = round(actual_final_price * (1.0 - dispute_penalty), 2)
        await self.db.decision_outcomes_extended.update_one(
            {"booking_id": booking_id},
            {
                "$set": {
                    "booking_id": booking_id,
                    "model_version": model_version,
                    "risk_version": int(decision.get("risk_version", 1)),
                    "is_canary": bool(decision.get("is_canary", False)),
                    "predicted_score": round(predicted_score, 2),
                    "actual_outcome": "success" if (actual_booking_result and not actual_dispute_flag) else "loss",
                    "revenue_impact": revenue_impact,
                    "gross_revenue": round(actual_final_price, 2),
                    "dispute_occurred": actual_dispute_flag,
                    "timestamp": now,
                },
                "$setOnInsert": {"_id": ObjectId()},
            },
            upsert=True,
        )

        await self.vendor_analytics_service.record_booking_outcome(
            vendor_id=booking["vendor_id"],
            category=category,
            completed=actual_completion_status == "completed",
            canceled=actual_completion_status in {"cancelled", "failed"},
        )
        if actual_dispute_flag:
            await self.vendor_analytics_service.record_milestone_status(
                vendor_id=booking["vendor_id"],
                category=category,
                delayed=False,
                disputed=True,
            )
        await self.profit_monitor_service.evaluate_profitability()

        logger.info("decision_outcome_recorded booking_id=%s model_version=%s", str(booking_id), model_version)
        return {"status": "ok", "booking_id": str(booking_id), "model_version": model_version}
