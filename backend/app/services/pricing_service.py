from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Any, Dict, List

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.schemas import PricingRequest
from app.utils.ids import oid

logger = logging.getLogger(__name__)


class PricingService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db

    async def compute_price_fairness(self, payload: PricingRequest) -> Dict[str, Any]:
        event_id = oid(payload.event_id)
        vendor_id = oid(payload.vendor_id)
        window_start = datetime.now(timezone.utc) - timedelta(days=120)

        quote_cursor = self.db.quotes.find(
            {
                "created_at": {"$gte": window_start},
                "status": {"$in": ["accepted", "expired", "declined", "pending"]},
                "category": payload.category,
                "city": payload.city,
            },
            projection={"amount": 1},
        ).limit(5000)
        quote_amounts = [float(q["amount"]) async for q in quote_cursor if q.get("amount")]

        analytics = await self.db.vendor_analytics.find_one(
            {"vendor_id": vendor_id},
            sort=[("day", -1)],
            projection={"average_quote": 1, "average_discount_pct": 1},
        )

        market_baseline = median(quote_amounts) if quote_amounts else payload.quoted_price
        vendor_baseline = float(analytics["average_quote"]) if analytics and analytics.get("average_quote") else market_baseline
        effective_baseline = (market_baseline * 0.65) + (vendor_baseline * 0.35)

        fairness_delta = ((payload.quoted_price - effective_baseline) / max(1.0, effective_baseline)) * 100.0
        price_fairness = max(0.0, min(100.0, 100.0 - abs(fairness_delta)))

        await self.db.quotes.update_one(
            {"event_id": event_id, "vendor_id": vendor_id, "status": {"$in": ["pending", "accepted"]}},
            {
                "$set": {
                    "event_id": event_id,
                    "vendor_id": vendor_id,
                    "category": payload.category,
                    "city": payload.city,
                    "amount": payload.quoted_price,
                    "status": "pending",
                    "updated_at": datetime.now(timezone.utc),
                },
                "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
            },
            upsert=True,
        )
        logger.info("price_fairness_computed event_id=%s vendor_id=%s fairness=%.2f", payload.event_id, payload.vendor_id, price_fairness)
        return {
            "event_id": payload.event_id,
            "vendor_id": payload.vendor_id,
            "price_fairness": round(price_fairness, 2),
            "market_baseline": round(market_baseline, 2),
            "vendor_baseline": round(vendor_baseline, 2),
            "quoted_price": payload.quoted_price,
        }

