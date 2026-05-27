from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

REDIS_QUEUE_KEY = "sdn:delivery_events"


async def emit_delivery_event(
    request: Request,
    *,
    event_type: str,
    payload: dict[str, Any],
    notify_user_ids: list[str],
    job_id: Optional[str] = None,
) -> None:
    """
    Fan-out: WebSocket hub + optional Redis queue for workers / push bridge.
    Does not import vendor or booking modules.
    """
    hub = getattr(request.app.state, "delivery_hub", None)
    envelope = {
        "type": event_type,
        "job_id": job_id,
        "payload": payload,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    if hub is not None:
        for uid in notify_user_ids:
            if uid:
                await hub.publish_to_user(str(uid), envelope)
        if job_id:
            await hub.publish_to_job(str(job_id), envelope)

    redis = getattr(request.app.state, "redis", None)
    if redis is not None:
        try:
            body = json.dumps(
                {"event_type": event_type, "job_id": job_id, "payload": payload, "notify": notify_user_ids},
                default=str,
            )
            await redis.lpush(REDIS_QUEUE_KEY, body.encode("utf-8"))
            await redis.ltrim(REDIS_QUEUE_KEY, 0, 49_999)
        except Exception:
            logger.debug("delivery_redis_queue_failed", exc_info=True)

    db: Optional[AsyncIOMotorDatabase] = getattr(request.app.state, "db", None)
    if db is not None:
        doc = {
            "id": f"nde_{uuid4().hex}",
            "event_type": event_type,
            "job_id": job_id,
            "payload": payload,
            "notify_user_ids": notify_user_ids,
            "created_at": datetime.now(timezone.utc),
        }
        try:
            await db["delivery_notification_outbox"].insert_one(doc)
        except Exception:
            logger.debug("delivery_outbox_write_failed", exc_info=True)
