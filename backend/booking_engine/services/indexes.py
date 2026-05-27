from __future__ import annotations

import logging
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING

logger = logging.getLogger(__name__)


async def ensure_booking_engine_indexes(db: AsyncIOMotorDatabase) -> None:
    now = datetime.now(timezone.utc)
    logger.info("ensuring_booking_engine_indexes", extra={"event": "booking_engine_indexes_start", "time": now.isoformat()})

    await db.be_booking_intents.create_index([("id", ASCENDING)], unique=True, name="uniq_be_booking_intents_id")
    await db.be_booking_intents.create_index([("user_id", ASCENDING), ("status", ASCENDING)], name="idx_be_intents_user_status")
    await db.be_booking_intents.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0, name="ttl_be_intents_expires")

    await db.be_bookings.create_index([("id", ASCENDING)], unique=True, name="uniq_be_bookings_id")
    await db.be_bookings.create_index([("intent_id", ASCENDING)], unique=True, name="uniq_be_bookings_intent_id")
    await db.be_bookings.create_index([("vendor_id", ASCENDING), ("status", ASCENDING)], name="idx_be_bookings_vendor_status")
    await db.be_bookings.create_index([("user_id", ASCENDING), ("status", ASCENDING)], name="idx_be_bookings_user_status")

    await db.be_payments.create_index([("intent_id", ASCENDING)], unique=True, name="uniq_be_payments_intent_id")
    await db.be_payments.create_index([("razorpay_order_id", ASCENDING)], unique=True, sparse=True, name="uniq_be_payments_order_id")
    await db.be_payments.create_index([("razorpay_payment_id", ASCENDING)], unique=True, sparse=True, name="uniq_be_payments_payment_id")

    await db.be_idempotency.create_index(
        [("user_id", ASCENDING), ("scope", ASCENDING), ("key", ASCENDING)],
        unique=True,
        name="uniq_be_idempotency",
    )
    await db.be_idempotency.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0, name="ttl_be_idempotency_expires")

    await db.be_locks.create_index([("lock_key", ASCENDING)], unique=True, name="uniq_be_locks_key")
    await db.be_locks.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0, name="ttl_be_locks_expires")
    await db.be_locks.create_index(
        [("vendor_id", ASCENDING), ("event_date", ASCENDING), ("start_time", ASCENDING), ("end_time", ASCENDING), ("state", ASCENDING)],
        name="idx_be_service_slot_conflict",
    )

    await db.be_inventory_reservations.create_index([("intent_id", ASCENDING)], unique=True, name="uniq_be_inventory_reservation_intent")
    await db.rental_inventory_windows.create_index([("item_id", ASCENDING), ("day", ASCENDING)], unique=True, name="uniq_rental_window_day")

    await db.be_state_transitions.create_index([("booking_id", ASCENDING), ("created_at", ASCENDING)], name="idx_be_state_transitions")
    await db.be_escrow_ledger.create_index([("booking_id", ASCENDING), ("status", ASCENDING)], name="idx_be_escrow_booking_status")

    await db.be_jobs.create_index([("job_type", ASCENDING), ("status", ASCENDING), ("run_after", ASCENDING)], name="idx_be_jobs_queue")

    logger.info("booking_engine_indexes_ready", extra={"event": "booking_engine_indexes_ready"})
