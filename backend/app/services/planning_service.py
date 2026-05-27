from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.core.exceptions import NotFoundError
from app.models.schemas import PlanningRequest
from app.utils.ids import oid

logger = logging.getLogger(__name__)


class PlanningService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db

    async def create_or_update_plan(self, payload: PlanningRequest) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        event_id = oid(payload.event_id)
        user_id = oid(payload.user_id)

        event = await self.db.events.find_one({"_id": event_id, "user_id": user_id})
        if not event:
            raise NotFoundError("Event not found for user")

        latest = await self.db.event_plans.find_one(
            {"event_id": event_id},
            sort=[("version", -1)],
            projection={"version": 1},
        )
        next_version = 1 if not latest else int(latest["version"]) + 1

        category_budget = payload.preferences.budget / max(1, len(payload.preferences.categories))
        allocations = {c: round(category_budget, 2) for c in payload.preferences.categories}
        ai_plan = {
            "allocations": allocations,
            "target_vendor_count_per_category": 5,
            "schedule_buffer_minutes": 45,
            "priority": "speed" if payload.event_date.timestamp() - now.timestamp() < 1209600 else "balanced",
        }

        plan_doc = {
            "event_id": event_id,
            "user_id": user_id,
            "version": next_version,
            "constraints": payload.preferences.model_dump(),
            "ai_plan": ai_plan,
            "updated_at": now,
        }
        await self.db.event_plans.insert_one(plan_doc)

        updated_event = await self.db.events.find_one_and_update(
            {"_id": event_id},
            {
                "$set": {
                    "status": "planning",
                    "attendee_count": payload.preferences.attendee_count,
                    "budget": payload.preferences.budget,
                    "categories": payload.preferences.categories,
                    "updated_at": now,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        logger.info("event_plan_created event_id=%s version=%s", payload.event_id, next_version)
        return {
            "event_id": payload.event_id,
            "version": next_version,
            "plan": ai_plan,
            "event_status": updated_event["status"] if updated_event else "planning",
        }

