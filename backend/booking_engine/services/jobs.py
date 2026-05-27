from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from booking_engine.core.state_machine import BookingStateMachine
from booking_engine.models.booking_models import ActorRole, BookingStatus, CategoryType
from booking_engine.services.escrow_service import EscrowService

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def schedule_sla_timeout_job(db: AsyncIOMotorDatabase, booking_id: str, minutes: int = 30) -> None:
    now = _now()
    await db.be_jobs.insert_one(
        {
            "job_type": "vendor_sla_timeout",
            "booking_id": booking_id,
            "status": "queued",
            "run_after": now + timedelta(minutes=minutes),
            "attempts": 0,
            "created_at": now,
            "updated_at": now,
        }
    )


async def schedule_refund_job(db: AsyncIOMotorDatabase, booking_id: str, reason: str) -> None:
    now = _now()
    await db.be_jobs.insert_one(
        {
            "job_type": "refund_processing",
            "booking_id": booking_id,
            "reason": reason,
            "status": "queued",
            "run_after": now,
            "attempts": 0,
            "created_at": now,
            "updated_at": now,
        }
    )


async def run_booking_engine_worker(db: AsyncIOMotorDatabase) -> None:
    state_machine = BookingStateMachine(db)
    escrow_service = EscrowService(db)

    while True:
        now = _now()
        job = await db.be_jobs.find_one_and_update(
            {"status": "queued", "run_after": {"$lte": now}},
            {"$set": {"status": "running", "updated_at": now}, "$inc": {"attempts": 1}},
            sort=[("run_after", 1)],
        )

        if not job:
            import asyncio

            await asyncio.sleep(2)
            continue

        try:
            if job["job_type"] == "vendor_sla_timeout":
                booking = await db.be_bookings.find_one({"id": job["booking_id"]}, {"_id": 0})
                if booking and booking["status"] == BookingStatus.VENDOR_PENDING.value:
                    updated = await state_machine.transition_booking(
                        booking_id=booking["id"],
                        category=CategoryType(booking["category_type"]),
                        actor=ActorRole.SYSTEM,
                        expected_status=BookingStatus.VENDOR_PENDING,
                        expected_version=booking["version"],
                        next_status=BookingStatus.CANCELLED,
                        reason="Vendor SLA timeout",
                        actor_id="booking_worker",
                    )
                    await schedule_refund_job(db, updated["id"], "Vendor did not respond in SLA")

            if job["job_type"] == "refund_processing":
                booking = await db.be_bookings.find_one({"id": job["booking_id"]}, {"_id": 0})
                if booking and booking["status"] in {
                    BookingStatus.CANCELLED.value,
                    BookingStatus.VENDOR_REJECTED.value,
                    BookingStatus.EXPIRED.value,
                    BookingStatus.REFUND_PENDING.value,
                }:
                    await escrow_service.mark_refund_pending(booking_id=booking["id"], reason=job.get("reason", "system_refund"))

            await db.be_jobs.update_one(
                {"_id": job["_id"]},
                {"$set": {"status": "done", "updated_at": _now()}},
            )
        except Exception as exc:
            logger.exception("booking_engine_job_failed", extra={"event": "booking_engine_job_failed", "job_type": job.get("job_type")})
            await db.be_jobs.update_one(
                {"_id": job["_id"]},
                {
                    "$set": {
                        "status": "queued" if job.get("attempts", 0) < 5 else "failed",
                        "last_error": str(exc),
                        "run_after": _now() + timedelta(minutes=2),
                        "updated_at": _now(),
                    }
                },
            )
