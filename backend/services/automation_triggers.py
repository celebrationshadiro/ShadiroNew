from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Dict, Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _schedule_id(prefix: str, ref_id: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{prefix}_{ref_id}_{stamp}"


async def schedule_quote_followup(db, quote: Dict[str, Any], hours: int = 24) -> None:
    run_at = datetime.now(timezone.utc) + timedelta(hours=hours)
    schedule = {
        "id": _schedule_id("quote_followup", quote.get("id", "unknown")),
        "type": "quote_followup",
        "run_at": run_at.isoformat(),
        "payload": {
            "message": "Reminder: Please respond to the pending quote request.",
            "user_id": quote.get("user_id"),
            "vendor_id": quote.get("vendor_id"),
            "channel": "email",
        },
        "status": "pending",
        "attempts": 0,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    await db.automation_schedules.insert_one(schedule)


async def schedule_quote_sla_alert(db, quote: Dict[str, Any], hours: int = 6) -> None:
    run_at = datetime.now(timezone.utc) + timedelta(hours=hours)
    schedule = {
        "id": _schedule_id("sla_alert", quote.get("id", "unknown")),
        "type": "sla_alert",
        "run_at": run_at.isoformat(),
        "payload": {
            "message": "SLA alert: Quote response overdue.",
            "vendor_id": quote.get("vendor_id"),
            "channel": "email",
        },
        "status": "pending",
        "attempts": 0,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    await db.automation_schedules.insert_one(schedule)
