from __future__ import annotations

import logging

from pymongo import ASCENDING, DESCENDING

from shadiro_delivery_network.constants import (
    COLLECTION_FRAUD,
    COLLECTION_JOBS,
    COLLECTION_PARTNERS,
    COLLECTION_QR_SESSIONS,
    COLLECTION_TRACKING,
)

logger = logging.getLogger(__name__)


async def ensure_delivery_indexes(db) -> None:
    """Isolated index lifecycle for Smart Delivery Network collections."""
    await db[COLLECTION_PARTNERS].create_index([("id", ASCENDING)], unique=True, sparse=True, name="uniq_delivery_partners_id")
    await db[COLLECTION_PARTNERS].create_index([("user_id", ASCENDING)], unique=True, sparse=True, name="uniq_delivery_partners_user")
    await db[COLLECTION_PARTNERS].create_index(
        [("status", ASCENDING), ("is_online", ASCENDING), ("updated_at", DESCENDING)],
        name="idx_delivery_partners_status_online",
    )

    await db[COLLECTION_JOBS].create_index([("id", ASCENDING)], unique=True, sparse=True, name="uniq_delivery_jobs_id")
    await db[COLLECTION_JOBS].create_index(
        [("vendor_id", ASCENDING), ("state", ASCENDING), ("created_at", DESCENDING)],
        name="idx_delivery_jobs_vendor_state",
    )
    await db[COLLECTION_JOBS].create_index(
        [("accepted_partner_id", ASCENDING), ("state", ASCENDING)],
        name="idx_delivery_jobs_partner_state",
    )
    await db[COLLECTION_JOBS].create_index(
        [("source_type", ASCENDING), ("source_order_id", ASCENDING)],
        name="idx_delivery_jobs_source",
    )

    await db[COLLECTION_QR_SESSIONS].create_index([("jti", ASCENDING)], unique=True, name="uniq_delivery_qr_jti")
    await db[COLLECTION_QR_SESSIONS].create_index(
        [("job_id", ASCENDING), ("vendor_id", ASCENDING)],
        name="idx_delivery_qr_job_vendor",
    )
    await db[COLLECTION_QR_SESSIONS].create_index(
        [("expires_at", ASCENDING)],
        expireAfterSeconds=0,
        name="ttl_delivery_qr_expires_at",
    )

    await db[COLLECTION_TRACKING].create_index(
        [("job_id", ASCENDING), ("recorded_at", DESCENDING)],
        name="idx_delivery_tracking_job_time",
    )

    await db[COLLECTION_FRAUD].create_index([("created_at", DESCENDING)], name="idx_delivery_fraud_created")
    await db[COLLECTION_FRAUD].create_index([("job_id", ASCENDING), ("event_type", ASCENDING)], name="idx_delivery_fraud_job_type")

    await db["delivery_notification_outbox"].create_index(
        [("created_at", DESCENDING)],
        name="idx_delivery_outbox_created",
    )

    logger.info("delivery_indexes_ensured", extra={"event": "delivery_indexes_ensured"})
