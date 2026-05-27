from __future__ import annotations

import logging
from datetime import datetime, timedelta
from core.database import build_mongo_manager
from core.cache import get_cache_service

logger = logging.getLogger(__name__)


async def release_expired_booking_locks() -> None:
    """
    Cron: runs every 5 minutes.
    Marks active locks that have expired as EXPIRED in MongoDB.
    """
    manager = build_mongo_manager()
    await manager.connect()
    try:
        db = manager.db
        from canonical_models.common import utcnow
        now = utcnow()
        
        res = await db.resource_locks.update_many(
            {"status": "ACTIVE", "expires_at": {"$lte": now}},
            {"$set": {"status": "EXPIRED", "released_at": now}}
        )
        logger.info(f"Cron: Released {res.modified_count} expired resource locks.")
    except Exception as e:
        logger.error(f"Error in release_expired_booking_locks cron task: {e}")
    finally:
        await manager.close()


async def update_vendor_availability_cache() -> None:
    """
    Cron: runs every 1 hour.
    Pre-warms and rebuilds availability cache indexes for all active vendors.
    """
    manager = build_mongo_manager()
    await manager.connect()
    try:
        db = manager.db
        cache = get_cache_service()
        current_month = datetime.now().strftime("%Y-%m")
        
        vendors = await db.vendors.find({"is_active": True}, {"id": 1}).to_list(length=1000)
        for vendor in vendors:
            vendor_id = vendor["id"]
            bookings = await db.bookings.find(
                {"vendor_id": vendor_id, "status": {"$in": ["CONFIRMED", "PAYMENT_RECEIVED", "IN_PROGRESS"]}},
                {"_id": 0, "id": 1, "scheduled_at": 1, "status": 1}
            ).to_list(length=200)
            
            locks = await db.resource_locks.find(
                {"entity_id": vendor_id, "status": "ACTIVE"},
                {"_id": 0, "id": 1, "expires_at": 1}
            ).to_list(length=100)
            
            data = {
                "vendor_id": vendor_id,
                "month": current_month,
                "bookings": bookings,
                "locks": locks,
            }
            await cache.set(f"availability:{vendor_id}:{current_month}", data, 30)
        logger.info("Cron: Rebuilt and cached availability for active vendors.")
    except Exception as e:
        logger.error(f"Error in update_vendor_availability_cache cron task: {e}")
    finally:
        await manager.close()


async def calculate_vendor_ratings() -> None:
    """
    Cron: runs every 24 hours.
    Aggregates review ratings dynamically to update cached average rating metrics on Vendor cards.
    """
    manager = build_mongo_manager()
    await manager.connect()
    try:
        db = manager.db
        pipeline = [
            {"$group": {
                "_id": "$vendor_id",
                "avg_rating": {"$avg": "$rating"},
                "total_reviews": {"$sum": 1}
            }}
        ]
        results = await db.reviews.aggregate(pipeline).to_list(length=5000)
        cache = get_cache_service()
        
        for res in results:
            vendor_id = res["_id"]
            avg = round(float(res["avg_rating"]), 2)
            total = int(res["total_reviews"])
            
            await db.vendors.update_one(
                {"id": vendor_id},
                {"$set": {"rating": avg, "avg_rating": avg, "total_reviews": total}}
            )
            # Invalidate vendor profile cache to reflect updated rating immediately
            await cache.delete(f"vendor:{vendor_id}")
            
        logger.info(f"Cron: Recalculated review metrics for {len(results)} vendors.")
    except Exception as e:
        logger.error(f"Error in calculate_vendor_ratings cron task: {e}")
    finally:
        await manager.close()


async def expire_old_quotes() -> None:
    """
    Cron: runs every 24 hours.
    Auto-expires responded or pending quotes older than 7 days (604800 seconds).
    """
    manager = build_mongo_manager()
    await manager.connect()
    try:
        db = manager.db
        from canonical_models.common import utcnow
        cutoff = utcnow() - timedelta(days=7)
        
        res = await db.quotes.update_many(
            {"status": {"$in": ["pending", "responded", "PENDING", "RESPONDED"]}, "created_at": {"$lte": cutoff}},
            {"$set": {"status": "expired"}}
        )
        logger.info(f"Cron: Auto-expired {res.modified_count} quotes older than 7 days.")
    except Exception as e:
        logger.error(f"Error in expire_old_quotes cron task: {e}")
    finally:
        await manager.close()
