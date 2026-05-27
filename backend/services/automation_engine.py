from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

ALLOWED_AUTOMATIONS = {
    "quote_followup",
    "booking_followup",
    "sla_alert",
    "event_reminder",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_run_at(value: str) -> datetime:
    return datetime.fromisoformat(value)


def normalize_schedule(payload: Dict[str, Any]) -> Dict[str, Any]:
    schedule_type = payload.get("type")
    if schedule_type not in ALLOWED_AUTOMATIONS:
        raise ValueError("Unsupported automation type")
    run_at = payload.get("run_at")
    if not run_at:
        raise ValueError("run_at is required")
    parsed_run_at = _parse_run_at(run_at)
    return {
        "id": payload.get("id"),
        "type": schedule_type,
        "run_at": parsed_run_at.isoformat(),
        "payload": payload.get("payload") or {},
        "status": payload.get("status") or "pending",
        "attempts": payload.get("attempts") or 0,
        "created_at": payload.get("created_at") or _now_iso(),
        "updated_at": payload.get("updated_at") or _now_iso(),
    }


async def execute_task(db, task: Dict[str, Any]) -> None:
    """Execute a scheduled automation task.

    Currently queues an internal notification with a generic message.
    """
    payload = task.get("payload") or {}
    channel = payload.get("channel", "email")
    message = payload.get("message") or f"Automation '{task.get('type')}' triggered."
    user_id = payload.get("user_id")
    vendor_id = payload.get("vendor_id")
    admin_id = payload.get("admin_id")

    notification = {
        "id": f"auto_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
        "channel": channel,
        "to": payload.get("to"),
        "user_id": user_id,
        "vendor_id": vendor_id,
        "admin_id": admin_id,
        "message": message,
        "type": task.get("type"),
        "created_at": _now_iso(),
        "status": "queued",
    }
    await db.notifications.insert_one(notification)


async def run_automation_worker(db, interval_seconds: int = 30):
    """Background loop to process due automations."""
    logger.info("Automation worker started")
    while True:
        now = datetime.now(timezone.utc).isoformat()
        cursor = db.automation_schedules.find(
            {"status": "pending", "run_at": {"$lte": now}},
            {"_id": 0},
        ).sort("run_at", 1).limit(50)
        tasks = await cursor.to_list(50)
        for task in tasks:
            try:
                await execute_task(db, task)
                await db.automation_schedules.update_one(
                    {"id": task["id"]},
                    {"$set": {"status": "completed", "updated_at": _now_iso()}},
                )
            except Exception as exc:
                logger.error("Automation task failed: %s", exc)
                await db.automation_schedules.update_one(
                    {"id": task["id"]},
                    {"$set": {"status": "failed", "updated_at": _now_iso(), "last_error": str(exc)}, "$inc": {"attempts": 1}},
                )
        await asyncio.sleep(interval_seconds)
