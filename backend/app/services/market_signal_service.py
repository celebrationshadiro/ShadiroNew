from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class MarketSignalService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db

    async def _compute_market_signal(self, category: str, city: str, as_of: datetime) -> Dict[str, Any]:
        day7 = as_of - timedelta(days=7)
        day14 = as_of - timedelta(days=14)
        day90 = as_of - timedelta(days=90)

        booking_pipeline_recent = [
            {"$match": {"created_at": {"$gte": day7}, "status": {"$in": ["confirmed", "completed", "in_progress"]}}},
            {"$lookup": {"from": "events", "localField": "event_id", "foreignField": "_id", "as": "event"}},
            {"$unwind": "$event"},
            {"$match": {"event.categories": category, "$or": [{"event.location.city": city}, {"event.city": city}]}},
            {"$count": "total"},
        ]
        booking_pipeline_prev = [
            {"$match": {"created_at": {"$gte": day14, "$lt": day7}, "status": {"$in": ["confirmed", "completed", "in_progress"]}}},
            {"$lookup": {"from": "events", "localField": "event_id", "foreignField": "_id", "as": "event"}},
            {"$unwind": "$event"},
            {"$match": {"event.categories": category, "$or": [{"event.location.city": city}, {"event.city": city}]}},
            {"$count": "total"},
        ]
        recent = await self.db.bookings.aggregate(booking_pipeline_recent, allowDiskUse=True).to_list(length=1)
        prev = await self.db.bookings.aggregate(booking_pipeline_prev, allowDiskUse=True).to_list(length=1)
        booking_volume_7d = int(recent[0]["total"]) if recent else 0
        booking_volume_prev_7d = int(prev[0]["total"]) if prev else 0
        city_surge_index = round(booking_volume_7d / max(1.0, booking_volume_prev_7d), 4)

        month = as_of.month
        seasonal_pipeline = [
            {"$match": {"created_at": {"$gte": day90}}},
            {"$lookup": {"from": "events", "localField": "event_id", "foreignField": "_id", "as": "event"}},
            {"$unwind": "$event"},
            {"$match": {"event.categories": category, "$or": [{"event.location.city": city}, {"event.city": city}]}},
            {"$group": {"_id": {"month": {"$month": "$created_at"}}, "count": {"$sum": 1}}},
        ]
        seasonal_rows = await self.db.bookings.aggregate(seasonal_pipeline, allowDiskUse=True).to_list(length=24)
        monthly_counts = [int(r.get("count", 0)) for r in seasonal_rows]
        current_month_count = sum(int(r.get("count", 0)) for r in seasonal_rows if int(r.get("_id", {}).get("month", 0)) == month)
        seasonal_multiplier = round(current_month_count / max(1.0, (sum(monthly_counts) / max(1, len(monthly_counts)))), 4)

        avail_recent_start = as_of - timedelta(days=3)
        avail_prev_start = as_of - timedelta(days=6)
        availability_recent = await self.db.vendor_availability.count_documents(
            {
                "city": city,
                "is_available": True,
                "service_date": {"$gte": avail_recent_start.date().isoformat()},
            }
        )
        availability_prev = await self.db.vendor_availability.count_documents(
            {
                "city": city,
                "is_available": True,
                "service_date": {"$gte": avail_prev_start.date().isoformat(), "$lt": avail_recent_start.date().isoformat()},
            }
        )
        availability_shrink_rate = round(
            max(0.0, min(1.0, (availability_prev - availability_recent) / max(1.0, availability_prev))),
            4,
        )
        demand_pressure = max(
            0.0,
            min(
                1.0,
                (city_surge_index * 0.45) + (min(2.0, seasonal_multiplier) / 2.0 * 0.30) + (availability_shrink_rate * 0.25),
            ),
        )
        return {
            "category": category,
            "city": city,
            "booking_volume_7d": booking_volume_7d,
            "city_surge_index": city_surge_index,
            "seasonal_multiplier": seasonal_multiplier,
            "availability_shrink_rate": availability_shrink_rate,
            "demand_pressure": round(demand_pressure, 4),
        }

    async def get_market_signal(self, category: str, city: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        cached = await self.db.market_signals.find_one(
            {"category": category, "city": city, "created_at": {"$gte": now - timedelta(hours=6)}},
            sort=[("created_at", -1)],
        )
        if cached:
            return cached
        metrics = await self._compute_market_signal(category, city, now)
        doc = {
            "_id": ObjectId(),
            **metrics,
            "created_at": now,
            "expires_at": now + timedelta(days=30),
        }
        await self.db.market_signals.insert_one(doc)
        logger.info("market_signal_computed category=%s city=%s pressure=%.4f", category, city, metrics["demand_pressure"])
        return doc

    async def get_price_forecast(self, category: str, city: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        signal = await self.get_market_signal(category, city)
        density_pipeline = [
            {"$match": {"city": city, "is_available": True}},
            {"$lookup": {"from": "vendor_profiles", "localField": "vendor_id", "foreignField": "vendor_id", "as": "profile"}},
            {"$unwind": "$profile"},
            {"$match": {"profile.service_categories": category}},
            {"$group": {"_id": "$service_date", "slots": {"$sum": 1}}},
        ]
        density_rows = await self.db.vendor_availability.aggregate(density_pipeline, allowDiskUse=True).to_list(length=60)
        total_slots = sum(int(r.get("slots", 0)) for r in density_rows)
        vendor_availability_density = total_slots / max(1.0, len(density_rows))

        historical_rows = await self.db.market_signals.find(
            {"category": category, "city": city, "created_at": {"$gte": now - timedelta(days=180)}},
            projection={"city_surge_index": 1, "seasonal_multiplier": 1, "demand_pressure": 1},
            limit=180,
        ).to_list(length=180)
        avg_surge = sum(float(r.get("city_surge_index", 1.0)) for r in historical_rows) / max(1, len(historical_rows))
        avg_pressure = sum(float(r.get("demand_pressure", 0.5)) for r in historical_rows) / max(1, len(historical_rows))

        scarcity_factor = max(0.0, min(1.0, 1.0 - min(1.0, vendor_availability_density / 40.0)))
        category_surge_index = float(signal.get("city_surge_index", 1.0))
        seasonal = float(signal.get("seasonal_multiplier", 1.0))

        predicted_7 = ((category_surge_index - 1.0) * 6.0) + (scarcity_factor * 4.0) + ((seasonal - 1.0) * 2.0)
        predicted_30 = ((avg_surge - 1.0) * 9.0) + (avg_pressure * 4.0) + ((seasonal - 1.0) * 3.0)
        predicted_7_day_change = round(max(-20.0, min(30.0, predicted_7)), 2)
        predicted_30_day_change = round(max(-35.0, min(45.0, predicted_30)), 2)

        return {
            "category": category,
            "city": city,
            "vendor_availability_density": round(vendor_availability_density, 4),
            "category_surge_index": round(category_surge_index, 4),
            "historical_surge_baseline": round(avg_surge, 4),
            "predicted_7_day_change": predicted_7_day_change,
            "predicted_30_day_change": predicted_30_day_change,
            "generated_at": now,
        }
