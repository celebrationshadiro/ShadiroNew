from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase

from shadiro_delivery_network.constants import COLLECTION_JOBS, COLLECTION_TRACKING


class TrackingService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._db = db

    async def append_location(
        self,
        *,
        job_id: str,
        partner_id: str,
        lat: float,
        lng: float,
        accuracy_m: Optional[float] = None,
        speed_mps: Optional[float] = None,
        heading: Optional[float] = None,
    ) -> str:
        pid = f"trk_{uuid4().hex}"
        doc = {
            "id": pid,
            "job_id": job_id,
            "partner_id": partner_id,
            "lat": lat,
            "lng": lng,
            "accuracy_m": accuracy_m,
            "speed_mps": speed_mps,
            "heading": heading,
            "recorded_at": datetime.now(timezone.utc),
        }
        await self._db[COLLECTION_TRACKING].insert_one(doc)
        await self._db[COLLECTION_JOBS].update_one(
            {"id": job_id},
            {
                "$set": {
                    "driver_last_lat": lat,
                    "driver_last_lng": lng,
                    "driver_last_at": doc["recorded_at"],
                    "updated_at": doc["recorded_at"],
                }
            },
        )
        return pid

    async def latest_for_job(self, job_id: str) -> Optional[dict[str, Any]]:
        cur = (
            self._db[COLLECTION_TRACKING]
            .find({"job_id": job_id}, {"_id": 0})
            .sort("recorded_at", -1)
            .limit(1)
        )
        docs = await cur.to_list(length=1)
        return docs[0] if docs else None
