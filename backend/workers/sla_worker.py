from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase

from core.config import get_settings
from core.database import build_mongo_manager
from core.state_machine import BookingStateMachine
from canonical_models.common import BookingIntentStatus, BookingStatus, ResourceLockStatus, UserRole, utcnow

logger = logging.getLogger(__name__)


def _safe_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    return None


async def _audit_log(
    *,
    db: AsyncIOMotorDatabase,
    action: str,
    entity_id: str,
    payload: dict[str, Any] | None = None,
) -> None:
    await db.audit_logs.insert_one(
        {
            "id": f"audit_{uuid4().hex}",
            "actor_id": "system",
            "actor_role": UserRole.SYSTEM.value,
            "action": action,
            "entity_type": "worker",
            "entity_id": entity_id,
            "payload": payload or {},
            "request_id": "sla_worker",
            "created_at": utcnow(),
        }
    )


async def _restore_reserved_stock_for_lock(db: AsyncIOMotorDatabase, lock_doc: dict[str, Any]) -> None:
    now = utcnow()
    vendor_id = lock_doc.get("vendor_id")
    for item in lock_doc.get("items", []):
        qty = int(item.get("qty", 0) or 0)
        if qty <= 0:
            continue
        await db.grocery_items.update_one(
            {"id": item.get("item_id"), "vendor_id": vendor_id},
            {
                "$inc": {"reserved_qty": -qty},
                "$set": {"updated_at": now},
            },
        )


async def _expire_or_release_lock(
    *,
    db: AsyncIOMotorDatabase,
    lock_doc: dict[str, Any],
    status: ResourceLockStatus,
    reason: str,
) -> bool:
    lock_id = str(lock_doc.get("id"))
    current_status = str(lock_doc.get("status", ""))
    if current_status != ResourceLockStatus.ACTIVE.value:
        return False

    if str(lock_doc.get("entity_type")) == "STOCK":
        await _restore_reserved_stock_for_lock(db, lock_doc)

    updated = await db.resource_locks.update_one(
        {"id": lock_id, "status": ResourceLockStatus.ACTIVE.value},
        {
            "$set": {
                "status": status.value,
                "released_at": utcnow(),
                "updated_at": utcnow(),
                "release_reason": reason,
            }
        },
    )
    return updated.modified_count == 1


async def _expire_stale_booking_intents(db: AsyncIOMotorDatabase, now: datetime) -> int:
    intents = await db.booking_intents.find(
        {
            "status": BookingIntentStatus.PENDING.value,
            "expires_at": {"$lte": now},
        },
        {"_id": 0},
    ).to_list(length=500)

    expired_count = 0
    for intent in intents:
        updated = await db.booking_intents.find_one_and_update(
            {
                "id": intent["id"],
                "status": BookingIntentStatus.PENDING.value,
            },
            {
                "$set": {
                    "status": BookingIntentStatus.EXPIRED.value,
                    "updated_at": now,
                },
                "$inc": {"version": 1},
            },
            projection={"_id": 0},
        )
        if not updated:
            continue

        expired_count += 1
        locks = await db.resource_locks.find(
            {
                "booking_intent_id": intent["id"],
                "status": ResourceLockStatus.ACTIVE.value,
            },
            {"_id": 0},
        ).to_list(length=200)

        for lock in locks:
            await _expire_or_release_lock(
                db=db,
                lock_doc=lock,
                status=ResourceLockStatus.EXPIRED,
                reason="booking_intent_expired",
            )

        await _audit_log(
            db=db,
            action="booking_intent_expired",
            entity_id=intent["id"],
            payload={"expired_at": now.isoformat()},
        )
    return expired_count


async def _cleanup_expired_resource_locks(db: AsyncIOMotorDatabase, now: datetime) -> int:
    locks = await db.resource_locks.find(
        {
            "status": ResourceLockStatus.ACTIVE.value,
            "expires_at": {"$lte": now},
        },
        {"_id": 0},
    ).to_list(length=500)

    cleaned = 0
    for lock in locks:
        ok = await _expire_or_release_lock(
            db=db,
            lock_doc=lock,
            status=ResourceLockStatus.EXPIRED,
            reason="lock_ttl_expired",
        )
        if ok:
            cleaned += 1
    return cleaned


def _resolve_vendor_sla_deadline(booking: dict[str, Any], default_minutes: int) -> datetime:
    meta = booking.get("meta") or {}
    due_at = _safe_datetime(meta.get("vendor_response_due_at"))
    if due_at:
        return due_at

    created_at = _safe_datetime(booking.get("created_at")) or utcnow()
    return created_at + timedelta(minutes=default_minutes)


async def _queue_refund_request(
    *,
    db: AsyncIOMotorDatabase,
    booking: dict[str, Any],
    reason: str,
) -> None:
    booking_id = str(booking.get("id"))
    existing = await db.refunds.find_one(
        {"booking_id": booking_id, "status": {"$in": ["REQUESTED", "PROCESSING", "COMPLETED"]}},
        {"_id": 0, "id": 1},
    )
    if existing:
        return

    payment = await db.payments.find_one({"booking_id": booking_id}, {"_id": 0})
    if not payment:
        return

    refund_doc = {
        "id": f"ref_{uuid4().hex}",
        "booking_id": booking_id,
        "payment_id": payment.get("id"),
        "razorpay_payment_id": payment.get("razorpay_payment_id"),
        "amount_paise": int(payment.get("amount", booking.get("amount_gross_paise", 0)) or 0),
        "status": "REQUESTED",
        "reason": reason,
        "requested_by": UserRole.SYSTEM.value,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    await db.refunds.insert_one(refund_doc)


async def _notify(
    db: AsyncIOMotorDatabase,
    *,
    user_id: str,
    title: str,
    body: str,
    meta: dict[str, Any] | None = None,
) -> None:
    await db.notifications.insert_one(
        {
            "id": f"notif_{uuid4().hex}",
            "user_id": user_id,
            "title": title,
            "body": body,
            "meta": meta or {},
            "created_at": utcnow(),
            "read": False,
        }
    )


async def _handle_rental_balance_due(
    db: AsyncIOMotorDatabase,
    now: datetime,
    grace_hours: int = 24,
) -> dict[str, int]:
    # Market default: deposit forfeited if balance unpaid.
    auto_cancel_refund_pct = 0
    reminded = 0
    auto_cancelled = 0

    cursor = db.bookings.find(
        {
            "category_type": "rental",
            "status": {"$nin": [BookingStatus.CANCELLED.value, BookingStatus.COMPLETED.value]},
            "meta.balance_amount_paise": {"$gt": 0},
            "meta.balance_paid": {"$ne": True},
            "meta.balance_due_at": {"$ne": None},
        },
        {"_id": 0},
    )
    rentals = await cursor.to_list(length=500)
    for booking in rentals:
        meta = booking.get("meta") or {}
        due_at = meta.get("balance_due_at")
        if not isinstance(due_at, datetime):
            continue

        if now >= due_at and not meta.get("balance_reminded"):
            await _notify(
                db,
                user_id=str(booking.get("user_id")),
                title="Rental balance due",
                body="Your rental balance is due. Please complete payment to keep the booking confirmed.",
                meta={"booking_id": booking.get("id")},
            )
            await db.bookings.update_one(
                {"id": booking["id"]},
                {"$set": {"meta.balance_reminded": True, "updated_at": now}, "$inc": {"version": 1}},
            )
            reminded += 1

        if now >= (due_at + timedelta(hours=grace_hours)):
            updated = await db.bookings.find_one_and_update(
                {"id": booking["id"], "version": int(booking.get("version", 1))},
                {"$set": {"status": BookingStatus.CANCELLED.value, "cancelled_at": now, "updated_at": now}, "$inc": {"version": 1}},
                projection={"_id": 0},
                return_document=True,
            )
            if updated:
                auto_cancelled += 1
                if auto_cancel_refund_pct > 0:
                    deposit_paise = int((updated.get("meta") or {}).get("deposit_amount_paise", 0) or 0)
                    refund_amount = (deposit_paise * auto_cancel_refund_pct) // 100
                    if refund_amount > 0:
                        await db.refunds.insert_one(
                            {
                                "id": f"ref_{uuid4().hex}",
                                "booking_id": updated["id"],
                                "amount_paise": refund_amount,
                                "status": "REQUESTED",
                                "reason": "rental_balance_unpaid_auto_cancel",
                                "requested_by": UserRole.SYSTEM.value,
                                "created_at": utcnow(),
                                "updated_at": utcnow(),
                            }
                        )
                await _audit_log(
                    db=db,
                    action="rental_auto_cancelled_balance_unpaid",
                    entity_id=updated["id"],
                    payload={"due_at": due_at.isoformat(), "grace_hours": grace_hours, "refund_pct": auto_cancel_refund_pct},
                )

    return {"rental_balance_reminded": reminded, "rental_auto_cancelled": auto_cancelled}


async def _cancel_vendor_sla_breached_bookings(
    db: AsyncIOMotorDatabase,
    now: datetime,
    vendor_sla_minutes: int,
) -> int:
    state_machine = BookingStateMachine(db)
    pending_vendor_response = await db.bookings.find(
        {"status": BookingStatus.PAYMENT_RECEIVED.value},
        {"_id": 0},
    ).to_list(length=500)

    cancelled = 0
    for booking in pending_vendor_response:
        deadline = _resolve_vendor_sla_deadline(booking, vendor_sla_minutes)
        if now < deadline:
            continue

        try:
            updated = await state_machine.transition_booking(
                booking_id=booking["id"],
                from_status=BookingStatus.PAYMENT_RECEIVED,
                to_status=BookingStatus.CANCELLED,
                actor_role=UserRole.SYSTEM,
                actor_id="sla_worker",
                current_version=int(booking.get("version", 1)),
                reason="Vendor SLA timeout",
            )
        except Exception:
            continue

        cancelled += 1
        await _queue_refund_request(
            db=db,
            booking=updated,
            reason="vendor_sla_timeout",
        )
        await _audit_log(
            db=db,
            action="booking_auto_cancelled_vendor_sla",
            entity_id=updated["id"],
            payload={"deadline": deadline.isoformat()},
        )
    return cancelled


async def run_sla_worker_once(
    db: AsyncIOMotorDatabase,
    *,
    vendor_sla_minutes: int = 30,
) -> dict[str, int]:
    now = utcnow()
    expired_intents = await _expire_stale_booking_intents(db, now)
    expired_locks = await _cleanup_expired_resource_locks(db, now)
    sla_cancelled = await _cancel_vendor_sla_breached_bookings(
        db,
        now,
        vendor_sla_minutes=vendor_sla_minutes,
    )
    rental_balance_stats = await _handle_rental_balance_due(db, now)
    return {
        "expired_intents": expired_intents,
        "expired_locks": expired_locks,
        "sla_cancelled": sla_cancelled,
        **rental_balance_stats,
    }


async def run_sla_worker(
    *,
    poll_interval_seconds: int = 15,
    vendor_sla_minutes: int = 30,
) -> None:
    settings = get_settings()
    manager = build_mongo_manager(settings)
    await manager.connect()
    await manager.ensure_indexes()
    if manager.db is None:
        raise RuntimeError("Database connection failed")

    db = manager.db
    logger.info("sla_worker_started", extra={"event": "sla_worker_started"})
    try:
        while True:
            try:
                stats = await run_sla_worker_once(
                    db,
                    vendor_sla_minutes=vendor_sla_minutes,
                )
                logger.info(
                    "sla_worker_tick",
                    extra={"event": "sla_worker_tick", **stats},
                )
            except Exception as exc:
                logger.exception(
                    "sla_worker_tick_failed",
                    extra={"event": "sla_worker_tick_failed", "error": str(exc)},
                )
            await asyncio.sleep(poll_interval_seconds)
    finally:
        await manager.close()
        logger.info("sla_worker_stopped", extra={"event": "sla_worker_stopped"})


if __name__ == "__main__":
    asyncio.run(run_sla_worker())
