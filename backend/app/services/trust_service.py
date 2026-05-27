from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.schemas import TrustScoreRequest
from app.utils.ids import oid

logger = logging.getLogger(__name__)


class TrustService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db

    async def compute_trust_score(self, payload: TrustScoreRequest) -> Dict[str, Any]:
        vendor_id = oid(payload.vendor_id)
        lookback = datetime.now(timezone.utc) - timedelta(days=180)

        bookings_count = await self.db.bookings.count_documents({"vendor_id": vendor_id, "created_at": {"$gte": lookback}})
        completed_count = await self.db.bookings.count_documents(
            {"vendor_id": vendor_id, "status": "completed", "updated_at": {"$gte": lookback}}
        )
        disputes = await self.db.escrow_transactions.count_documents(
            {"booking_id": {"$exists": True}, "vendor_id": vendor_id, "tx_type": "dispute", "created_at": {"$gte": lookback}}
        )

        analytics = await self.db.vendor_analytics.find(
            {"vendor_id": vendor_id, "day": {"$gte": lookback.date().isoformat()}},
            projection={
                "booking_count": 1,
                "quote_count": 1,
                "average_discount_pct": 1,
                "avg_response_time": 1,
                "counter_offer_frequency": 1,
                "avg_discount_given": 1,
                "cancellation_rate": 1,
                "milestone_delay_rate": 1,
                "dispute_ratio": 1,
            },
        ).to_list(length=180)
        quotes = max(1, sum(int(day.get("quote_count", 0)) for day in analytics))
        conversion_rate = sum(int(day.get("booking_count", 0)) for day in analytics) / quotes
        avg_response_time = sum(float(day.get("avg_response_time", 0.0)) for day in analytics) / max(1, len(analytics))
        counter_offer_frequency = sum(float(day.get("counter_offer_frequency", 0.0)) for day in analytics) / max(1, len(analytics))
        avg_discount_given = sum(float(day.get("avg_discount_given", 0.0)) for day in analytics) / max(1, len(analytics))
        cancellation_rate = sum(float(day.get("cancellation_rate", 0.0)) for day in analytics) / max(1, len(analytics))
        milestone_delay_rate = sum(float(day.get("milestone_delay_rate", 0.0)) for day in analytics) / max(1, len(analytics))
        dispute_ratio = sum(float(day.get("dispute_ratio", 0.0)) for day in analytics) / max(1, len(analytics))

        completion_rate = completed_count / max(1, bookings_count)
        dispute_rate = disputes / max(1, bookings_count)
        response_score = max(0.0, min(1.0, 1.0 - (avg_response_time / 240.0)))
        reliability_score = max(
            0.0,
            min(
                1.0,
                1.0 - ((cancellation_rate * 0.5) + (milestone_delay_rate * 0.25) + (dispute_ratio * 0.25)),
            ),
        )
        discount_stability = max(0.0, min(1.0, 1.0 - min(avg_discount_given / 50.0, 1.0)))
        score = (
            (completion_rate * 34.0)
            + (conversion_rate * 20.0)
            + ((1.0 - min(1.0, dispute_rate * 5.0)) * 16.0)
            + (response_score * 12.0)
            + (reliability_score * 12.0)
            + (discount_stability * 6.0)
        )
        score = max(0.0, min(100.0, score))

        doc = {
            "vendor_id": vendor_id,
            "score": round(score, 2),
            "signals": {
                "completion_rate": round(completion_rate, 4),
                "conversion_rate": round(conversion_rate, 4),
                "dispute_rate": round(dispute_rate, 4),
                "avg_response_time": round(avg_response_time, 2),
                "counter_offer_frequency": round(counter_offer_frequency, 4),
                "avg_discount_given": round(avg_discount_given, 2),
                "cancellation_rate": round(cancellation_rate, 4),
                "milestone_delay_rate": round(milestone_delay_rate, 4),
                "dispute_ratio": round(dispute_ratio, 4),
            },
            "updated_at": datetime.now(timezone.utc),
        }
        await self.db.trust_scores.update_one({"vendor_id": vendor_id}, {"$set": doc}, upsert=True)
        logger.info("trust_score_computed vendor_id=%s score=%.2f", payload.vendor_id, score)
        return {"vendor_id": payload.vendor_id, **doc}
