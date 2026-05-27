from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class VendorAnalyticsService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db

    @staticmethod
    def _day_key(ts: datetime) -> str:
        return ts.date().isoformat()

    async def record_negotiation_counter(
        self,
        vendor_id,
        category: str,
        discount_pct: float,
        response_time_minutes: float,
        accepted_probability: float,
    ) -> None:
        now = datetime.now(timezone.utc)
        day = self._day_key(now)
        update = {
            "$setOnInsert": {
                "vendor_id": vendor_id,
                "day": day,
                "category": category,
                "quote_count": 0,
                "booking_count": 0,
                "cancellations": 0,
                "counter_offer_count": 0,
                "negotiation_round_count": 0,
                "discount_samples": 0,
                "discount_total_pct": 0.0,
                "response_samples": 0,
                "response_total_minutes": 0.0,
                "milestone_total": 0,
                "milestone_delayed_count": 0,
                "dispute_count": 0,
                "completed_booking_count": 0,
                "average_quote": 0.0,
            },
            "$inc": {
                "counter_offer_count": 1,
                "negotiation_round_count": 1,
                "discount_samples": 1,
                "discount_total_pct": max(0.0, discount_pct),
                "response_samples": 1,
                "response_total_minutes": max(0.0, response_time_minutes),
                "acceptance_probability_sum": max(0.0, min(1.0, accepted_probability)),
            },
            "$set": {"updated_at": now},
        }
        await self.db.vendor_analytics.update_one({"vendor_id": vendor_id, "day": day}, update, upsert=True)
        await self._refresh_derived_metrics(vendor_id, day)

    async def record_booking_outcome(self, vendor_id, category: str, completed: bool, canceled: bool) -> None:
        now = datetime.now(timezone.utc)
        day = self._day_key(now)
        await self.db.vendor_analytics.update_one(
            {"vendor_id": vendor_id, "day": day},
            {
                "$setOnInsert": {
                    "vendor_id": vendor_id,
                    "day": day,
                    "category": category,
                    # booking_count, cancellations, completed_booking_count are NOT listed here
                    # because they also appear in $inc. MongoDB forbids path overlaps between
                    # $setOnInsert and $inc in the same upsert.  $inc already defaults to 0 for
                    # missing fields, so explicit initialisation is unnecessary.
                    "quote_count": 0,
                },
                "$inc": {
                    "booking_count": 1 if completed else 0,
                    "completed_booking_count": 1 if completed else 0,
                    "cancellations": 1 if canceled else 0,
                },
                "$set": {"updated_at": now},
            },
            upsert=True,
        )
        await self._refresh_derived_metrics(vendor_id, day)


    async def record_milestone_status(self, vendor_id, category: str, delayed: bool, disputed: bool) -> None:
        now = datetime.now(timezone.utc)
        day = self._day_key(now)
        await self.db.vendor_analytics.update_one(
            {"vendor_id": vendor_id, "day": day},
            {
                "$setOnInsert": {"vendor_id": vendor_id, "day": day, "category": category},
                "$inc": {
                    "milestone_total": 1,
                    "milestone_delayed_count": 1 if delayed else 0,
                    "dispute_count": 1 if disputed else 0,
                },
                "$set": {"updated_at": now},
            },
            upsert=True,
        )
        await self._refresh_derived_metrics(vendor_id, day)

    async def _refresh_derived_metrics(self, vendor_id, day: str) -> None:
        doc = await self.db.vendor_analytics.find_one(
            {"vendor_id": vendor_id, "day": day},
            projection={
                "response_total_minutes": 1,
                "response_samples": 1,
                "counter_offer_count": 1,
                "negotiation_round_count": 1,
                "discount_total_pct": 1,
                "discount_samples": 1,
                "cancellations": 1,
                "booking_count": 1,
                "milestone_total": 1,
                "milestone_delayed_count": 1,
                "dispute_count": 1,
                "completed_booking_count": 1,
            },
        )
        if not doc:
            return

        response_samples = int(doc.get("response_samples", 0))
        negotiation_round_count = int(doc.get("negotiation_round_count", 0))
        discount_samples = int(doc.get("discount_samples", 0))
        booking_count = int(doc.get("booking_count", 0))
        milestone_total = int(doc.get("milestone_total", 0))
        completed_booking_count = int(doc.get("completed_booking_count", 0))

        avg_response_time = float(doc.get("response_total_minutes", 0.0)) / max(1, response_samples)
        counter_offer_frequency = float(doc.get("counter_offer_count", 0)) / max(1, negotiation_round_count)
        avg_discount_given = float(doc.get("discount_total_pct", 0.0)) / max(1, discount_samples)
        cancellation_rate = float(doc.get("cancellations", 0)) / max(1, booking_count + completed_booking_count)
        milestone_delay_rate = float(doc.get("milestone_delayed_count", 0)) / max(1, milestone_total)
        dispute_ratio = float(doc.get("dispute_count", 0)) / max(1, completed_booking_count + int(doc.get("dispute_count", 0)))

        await self.db.vendor_analytics.update_one(
            {"vendor_id": vendor_id, "day": day},
            {
                "$set": {
                    "avg_response_time": round(avg_response_time, 2),
                    "counter_offer_frequency": round(counter_offer_frequency, 4),
                    "avg_discount_given": round(avg_discount_given, 2),
                    "cancellation_rate": round(cancellation_rate, 4),
                    "milestone_delay_rate": round(milestone_delay_rate, 4),
                    "dispute_ratio": round(dispute_ratio, 4),
                }
            },
        )

