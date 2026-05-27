from __future__ import annotations

import logging
from core.database import build_mongo_manager

logger = logging.getLogger(__name__)


async def update_vendor_booking_count(vendor_id: str) -> None:
    """
    Background job to update vendor booking count cache.
    Keeps total count off of the critical write lifecycle.
    """
    manager = build_mongo_manager()
    await manager.connect()
    try:
        db = manager.db
        count = await db.bookings.count_documents({
            "vendor_id": vendor_id,
            "status": {"$in": ["CONFIRMED", "PAYMENT_RECEIVED", "IN_PROGRESS", "COMPLETED"]}
        })
        await db.vendors.update_one(
            {"id": vendor_id},
            {"$set": {"total_bookings": count, "booking_count": count}}
        )
        logger.info(f"Successfully updated vendor {vendor_id} booking count to {count}")
    except Exception as e:
        logger.error(f"Error in update_vendor_booking_count task for vendor {vendor_id}: {e}")
    finally:
        await manager.close()


async def release_expired_locks(lock_ids: list[str]) -> None:
    """
    Background job to release expired resource locks.
    """
    manager = build_mongo_manager()
    await manager.connect()
    try:
        db = manager.db
        from canonical_models.common import utcnow
        now = utcnow()
        res = await db.resource_locks.update_many(
            {"id": {"$in": lock_ids}, "expires_at": {"$lte": now}, "status": "ACTIVE"},
            {"$set": {"status": "RELEASED", "released_at": now}}
        )
        logger.info(f"Released {res.modified_count} expired locks out of {len(lock_ids)}")
    except Exception as e:
        logger.error(f"Error in release_expired_locks task: {e}")
    finally:
        await manager.close()
