"""Migration: backfill vendor_type and move legacy grocery_items into grocery_items collection."""
import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
db_name = os.environ.get("DB_NAME", "shadiro_production")

PRODUCT_CATEGORY_IDS = {"cat-grocery", "grocery"}

logger = logging.getLogger(__name__)


def resolve_vendor_type(category_id):
    if category_id in PRODUCT_CATEGORY_IDS:
        return "product_vendor"
    if category_id:
        return "service_vendor"
    logger.warning("Vendor type could not be resolved; defaulting to service_vendor")
    return "service_vendor"


def parse_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_item(raw, vendor_id):
    name = raw.get("name") or raw.get("title")
    if not name:
        return None
    item_id = raw.get("id") or str(uuid.uuid4())
    stock_qty = parse_int(raw.get("stock_qty") if raw.get("stock_qty") is not None else raw.get("stock"), 0)
    availability = raw.get("availability")
    is_available = raw.get("is_available")
    if not isinstance(is_available, bool):
        if availability:
            is_available = availability != "out_of_stock"
        else:
            is_available = True
    return {
        "id": item_id,
        "vendor_id": vendor_id,
        "name": name,
        "category": raw.get("category") or raw.get("category_name"),
        "unit": raw.get("unit") or raw.get("uom") or "kg",
        "unit_price": parse_float(raw.get("unit_price") if raw.get("unit_price") is not None else raw.get("price"), 0.0),
        "stock_qty": stock_qty,
        "is_available": is_available,
        "image_url": raw.get("image_url") or raw.get("image"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


async def migrate():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    vendor_updates = 0
    item_inserts = 0

    cursor = db.vendors.find({}, {"_id": 0})
    async for vendor in cursor:
        vendor_id = vendor.get("id")
        category_id = vendor.get("category_id")
        resolved_type = resolve_vendor_type(category_id)
        existing_type = vendor.get("vendor_type")
        if existing_type and existing_type != resolved_type:
            logger.warning(
                "Vendor type mismatch for vendor_id=%s category_id=%s existing=%s resolved=%s",
                vendor_id,
                category_id,
                existing_type,
                resolved_type,
            )
        if existing_type != resolved_type:
            await db.vendors.update_one({"id": vendor_id}, {"$set": {"vendor_type": resolved_type}})
            vendor_updates += 1

        if category_id not in PRODUCT_CATEGORY_IDS:
            continue

        legacy_items = []
        legacy_items.extend(vendor.get("grocery_items") or [])
        legacy_items.extend(vendor.get("details", {}).get("product_catalog") or [])

        for raw in legacy_items:
            doc = normalize_item(raw or {}, vendor_id)
            if not doc:
                continue
            result = await db.grocery_items.update_one(
                {"id": doc["id"], "vendor_id": vendor_id},
                {"$setOnInsert": doc},
                upsert=True,
            )
            if result.upserted_id is not None:
                item_inserts += 1

    print(f"Updated vendor_type for {vendor_updates} vendors")
    print(f"Inserted {item_inserts} grocery items")

    client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
