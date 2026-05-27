from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.core.config import Settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.schemas import NegotiationRequest
from app.services.vendor_analytics_service import VendorAnalyticsService
from app.utils.ids import oid

logger = logging.getLogger(__name__)


class NegotiationService:
    def __init__(self, db: AsyncIOMotorDatabase, settings: Settings, vendor_analytics_service: VendorAnalyticsService) -> None:
        self.db = db
        self.settings = settings
        self.vendor_analytics_service = vendor_analytics_service

    async def _acceptance_probability(self, vendor_id, offer: float) -> float:
        pipeline = [
            {"$match": {"vendor_id": vendor_id}},
            {
                "$group": {
                    "_id": None,
                    "bookings": {"$sum": "$booking_count"},
                    "quotes": {"$sum": "$quote_count"},
                    "avg_discount": {"$avg": "$average_discount_pct"},
                    "avg_response_time": {"$avg": "$avg_response_time"},
                    "counter_offer_frequency": {"$avg": "$counter_offer_frequency"},
                    "cancellation_rate": {"$avg": "$cancellation_rate"},
                    "dispute_ratio": {"$avg": "$dispute_ratio"},
                }
            },
        ]
        data = await self.db.vendor_analytics.aggregate(pipeline, allowDiskUse=True).to_list(length=1)
        if not data:
            return 0.55
        row = data[0]
        conversion = float(row.get("bookings", 0)) / max(1.0, float(row.get("quotes", 1)))
        avg_discount = float(row.get("avg_discount", 0.0))
        discount_penalty = min(0.35, max(0.0, (avg_discount / 100.0) * 0.4))
        response_bonus = max(-0.10, min(0.10, (120.0 - float(row.get("avg_response_time", 120.0))) / 1200.0))
        counter_bonus = max(-0.08, min(0.08, float(row.get("counter_offer_frequency", 0.5)) - 0.5))
        reliability_penalty = min(0.25, (float(row.get("cancellation_rate", 0.0)) * 0.15) + (float(row.get("dispute_ratio", 0.0)) * 0.10))
        probability = max(0.05, min(0.98, conversion + 0.4 - discount_penalty + response_bonus + counter_bonus - reliability_penalty))
        if offer < 1:
            probability = 0.05
        return probability

    async def negotiate(self, payload: NegotiationRequest) -> Dict[str, Any]:
        vendor_id = oid(payload.vendor_id)
        event_id = oid(payload.event_id)
        profile = await self.db.vendor_profiles.find_one({"vendor_id": vendor_id})
        if not profile:
            raise NotFoundError("Vendor profile not found")

        config = profile.get("pricing_config", {})
        min_price = float(config.get("min_price", payload.initial_offer * 0.85))
        max_discount = float(config.get("max_discount", 15.0))
        if payload.initial_offer < min_price * 0.6:
            raise ValidationError("Offer too low for negotiation start")

        target_offer = payload.customer_target if payload.customer_target else payload.initial_offer
        requested_discount_pct = payload.requested_discount_pct
        if requested_discount_pct is None:
            requested_discount_pct = max(0.0, ((payload.initial_offer - target_offer) / payload.initial_offer) * 100.0)

        applied_discount = min(max_discount, requested_discount_pct)
        counter_offer = max(min_price, round(payload.initial_offer * (1 - applied_discount / 100.0), 2))
        acceptance_probability = await self._acceptance_probability(vendor_id, counter_offer)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self.settings.negotiation_ttl_seconds)

        round_doc = {
            "round": int(now.timestamp()),
            "offer": payload.initial_offer,
            "counter": counter_offer,
            "requested_discount_pct": round(requested_discount_pct, 2),
            "applied_discount_pct": round(applied_discount, 2),
            "accepted_probability": round(acceptance_probability, 4),
            "created_at": now,
        }

        previous_negotiation = await self.db.negotiations.find_one(
            {"event_id": event_id, "vendor_id": vendor_id, "status": {"$in": ["open", "countered"]}},
            projection={"last_activity_at": 1},
        )
        response_time_minutes = 60.0
        if previous_negotiation and previous_negotiation.get("last_activity_at"):
            response_time_minutes = max(
                0.0,
                (now - previous_negotiation["last_activity_at"]).total_seconds() / 60.0,
            )

        negotiation = await self.db.negotiations.find_one_and_update(
            {"event_id": event_id, "vendor_id": vendor_id, "status": {"$in": ["open", "countered"]}},
            {
                "$set": {
                    "event_id": event_id,
                    "vendor_id": vendor_id,
                    "status": "countered",
                    "current_offer": counter_offer,
                    "last_activity_at": now,
                    "expires_at": expires_at,
                },
                "$push": {"rounds": round_doc},
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        await self.vendor_analytics_service.record_negotiation_counter(
            vendor_id=vendor_id,
            category=profile.get("primary_category", "general"),
            discount_pct=applied_discount,
            response_time_minutes=response_time_minutes,
            accepted_probability=acceptance_probability,
        )

        logger.info("negotiation_countered event_id=%s vendor_id=%s counter=%s", payload.event_id, payload.vendor_id, counter_offer)
        return {
            "negotiation_id": str(negotiation["_id"]),
            "event_id": payload.event_id,
            "vendor_id": payload.vendor_id,
            "counter_offer": counter_offer,
            "acceptance_probability": round(acceptance_probability, 4),
            "max_discount": max_discount,
            "min_price": min_price,
            "status": negotiation["status"],
        }

    async def get_current_probability(self, event_id: str, vendor_id: str, fallback_price: Optional[float] = None) -> float:
        event_oid = oid(event_id)
        vendor_oid = oid(vendor_id)
        negotiation = await self.db.negotiations.find_one(
            {"event_id": event_oid, "vendor_id": vendor_oid, "status": {"$in": ["open", "countered", "accepted"]}},
            projection={"rounds": {"$slice": -1}, "current_offer": 1},
        )
        if negotiation and negotiation.get("rounds"):
            return float(negotiation["rounds"][-1].get("accepted_probability", 0.55))
        price = fallback_price if fallback_price else 1.0
        return await self._acceptance_probability(vendor_oid, price)
