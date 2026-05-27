from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.schemas import AvailabilityRequest
from app.utils.ids import oid

logger = logging.getLogger(__name__)


class AvailabilityService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db

    async def check_realtime_availability(self, payload: AvailabilityRequest) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        base_filter: Dict[str, Any] = {
            "city": payload.city,
            "is_available": True,
            "slot_start": {"$lte": payload.start_at},
            "slot_end": {"$gte": payload.end_at},
            "$or": [{"expires_at": {"$exists": False}}, {"expires_at": {"$gt": now}}],
        }
        if payload.vendor_ids:
            base_filter["vendor_id"] = {"$in": [oid(v) for v in payload.vendor_ids]}

        pipeline = [
            {"$match": base_filter},
            {
                "$lookup": {
                    "from": "vendor_profiles",
                    "localField": "vendor_id",
                    "foreignField": "vendor_id",
                    "as": "profile",
                }
            },
            {"$unwind": "$profile"},
            {"$match": {"profile.service_categories": payload.category}},
            {
                "$project": {
                    "_id": 0,
                    "vendor_id": {"$toString": "$vendor_id"},
                    "capacity_remaining": 1,
                    "availability_confidence": {
                        "$round": [
                            {
                                "$min": [
                                    1.0,
                                    {
                                        "$add": [
                                            {"$multiply": ["$confidence", 0.7]},
                                            {"$multiply": [{"$cond": [{"$gte": ["$capacity_remaining", 1]}, 1, 0]}, 0.3]},
                                        ]
                                    },
                                ]
                            },
                            4,
                        ]
                    },
                    "updated_at": 1,
                }
            },
            {"$sort": {"availability_confidence": -1, "updated_at": -1}},
        ]

        matches: List[Dict[str, Any]] = await self.db.vendor_availability.aggregate(pipeline, allowDiskUse=True).to_list(length=1000)
        result = {
            "event_id": payload.event_id,
            "count": len(matches),
            "vendors": matches,
        }
        logger.info("availability_checked event_id=%s matches=%s", payload.event_id, len(matches))
        return result

