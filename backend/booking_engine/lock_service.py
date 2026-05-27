from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid date format") from exc


def _parse_time(value: str) -> time:
    try:
        return time.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid time format") from exc


def _date_range_days(check_in: str, check_out: str) -> list[str]:
    start = _parse_date(check_in)
    end = _parse_date(check_out)
    if end <= start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="check_out must be greater than check_in",
        )
    days: list[str] = []
    cursor = start
    while cursor < end:
        days.append(cursor.isoformat())
        cursor = cursor + timedelta(days=1)
    return days


async def acquire_slot_lock(
    db: AsyncIOMotorDatabase,
    vendor_id: str,
    date_value: str,
    intent_id: str,
    ttl_min: int = 30,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, Any]:
    start_t = _parse_time(start_time or "00:00")
    end_t = _parse_time(end_time or "23:59")
    if end_t <= start_t:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid time range")

    now = utcnow()
    expires_at = now + timedelta(minutes=ttl_min)
    lock_id = f"lock_{uuid4().hex}"

    conflict = await db.resource_locks.find_one(
        {
            "entity_type": "SLOT",
            "vendor_id": vendor_id,
            "date": date_value,
            "status": "ACTIVE",
            "$or": [
                {"end_time": {"$gt": start_t.isoformat()}, "start_time": {"$lt": end_t.isoformat()}},
                {"start_time": None, "end_time": None},
            ],
        },
        {"_id": 0, "id": 1},
    )
    if conflict:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Requested slot is already locked")

    doc = {
        "id": lock_id,
        "entity_type": "SLOT",
        "entity_id": f"{vendor_id}:{date_value}",
        "booking_intent_id": intent_id,
        "vendor_id": vendor_id,
        "date": date_value,
        "start_time": start_t.isoformat(),
        "end_time": end_t.isoformat(),
        "locked_qty": 1,
        "status": "ACTIVE",
        "expires_at": expires_at,
        "released_at": None,
        "created_at": now,
        "updated_at": now,
    }
    try:
        await db.resource_locks.insert_one(doc)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Unable to acquire slot lock") from exc

    return {"lock_id": lock_id, "expires_at": expires_at}


async def acquire_date_range_lock(
    db: AsyncIOMotorDatabase,
    item_id: str,
    check_in: str,
    check_out: str,
    intent_id: str,
    ttl_min: int = 20,
) -> dict[str, Any]:
    days = _date_range_days(check_in, check_out)
    now = utcnow()
    expires_at = now + timedelta(minutes=ttl_min)
    lock_id = f"lock_{uuid4().hex}"

    conflict = await db.resource_locks.find_one(
        {
            "entity_type": "SLOT",
            "entity_id": item_id,
            "status": "ACTIVE",
            "date": {"$in": days},
        },
        {"_id": 0, "id": 1},
    )
    if conflict:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Date range unavailable")

    lock_docs = [
        {
            "id": f"{lock_id}:{d}",
            "group_lock_id": lock_id,
            "entity_type": "SLOT",
            "entity_id": item_id,
            "booking_intent_id": intent_id,
            "date": d,
            "locked_qty": 1,
            "status": "ACTIVE",
            "expires_at": expires_at,
            "released_at": None,
            "created_at": now,
            "updated_at": now,
        }
        for d in days
    ]
    try:
        await db.resource_locks.insert_many(lock_docs, ordered=True)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Unable to lock date range") from exc

    return {"lock_id": lock_id, "days": days, "expires_at": expires_at}


async def acquire_stock_lock(
    db: AsyncIOMotorDatabase,
    vendor_id: str,
    items: list[dict[str, Any]],
    intent_id: str,
    ttl_min: int = 15,
) -> dict[str, Any]:
    if not items:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="items required")

    now = utcnow()
    expires_at = now + timedelta(minutes=ttl_min)
    lock_id = f"lock_{uuid4().hex}"
    locked_items: list[dict[str, Any]] = []

    for item in items:
        item_id = str(item.get("item_id"))
        qty = int(item.get("qty", 0) or 0)
        if qty <= 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="qty must be > 0")

        updated = await db.grocery_items.find_one_and_update(
            {
                "id": item_id,
                "vendor_id": vendor_id,
                "$expr": {
                    "$gte": [
                        {"$subtract": [{"$subtract": ["$total_qty", "$reserved_qty"]}, "$sold_qty"]},
                        qty,
                    ]
                },
            },
            {
                "$inc": {"reserved_qty": qty},
                "$set": {"updated_at": now},
            },
            projection={"_id": 0, "id": 1},
        )
        if not updated:
            for rollback in locked_items:
                await db.grocery_items.update_one(
                    {"id": rollback["item_id"], "vendor_id": vendor_id},
                    {"$inc": {"reserved_qty": -int(rollback["qty"])}, "$set": {"updated_at": utcnow()}},
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Insufficient stock for item {item_id}",
            )
        locked_items.append({"item_id": item_id, "qty": qty})

    doc = {
        "id": lock_id,
        "entity_type": "STOCK",
        "entity_id": vendor_id,
        "booking_intent_id": intent_id,
        "vendor_id": vendor_id,
        "items": locked_items,
        "locked_qty": sum(int(i["qty"]) for i in locked_items),
        "status": "ACTIVE",
        "expires_at": expires_at,
        "released_at": None,
        "created_at": now,
        "updated_at": now,
    }
    await db.resource_locks.insert_one(doc)
    return {"lock_id": lock_id, "items": locked_items, "expires_at": expires_at}


async def release_lock(db: AsyncIOMotorDatabase, lock_id: str) -> bool:
    now = utcnow()
    lock_doc = await db.resource_locks.find_one(
        {
            "$or": [
                {"id": lock_id},
                {"group_lock_id": lock_id},
            ],
            "status": "ACTIVE",
        },
        {"_id": 0},
    )
    if not lock_doc:
        return False

    query = {"$or": [{"id": lock_id}, {"group_lock_id": lock_id}], "status": "ACTIVE"}
    docs = await db.resource_locks.find(query, {"_id": 0}).to_list(length=1000)

    for doc in docs:
        if doc.get("entity_type") == "STOCK":
            for item in doc.get("items", []):
                await db.grocery_items.update_one(
                    {"id": item.get("item_id"), "vendor_id": doc.get("vendor_id")},
                    {"$inc": {"reserved_qty": -int(item.get("qty", 0) or 0)}, "$set": {"updated_at": now}},
                )

    res = await db.resource_locks.update_many(
        query,
        {
            "$set": {
                "status": "RELEASED",
                "released_at": now,
                "updated_at": now,
            }
        },
    )
    return res.modified_count > 0


async def restore_stock_on_expire(db: AsyncIOMotorDatabase) -> int:
    now = utcnow()
    expired = await db.resource_locks.find(
        {
            "entity_type": "STOCK",
            "status": "ACTIVE",
            "expires_at": {"$lte": now},
        },
        {"_id": 0},
    ).to_list(length=1000)

    restored = 0
    for lock in expired:
        for item in lock.get("items", []):
            await db.grocery_items.update_one(
                {"id": item.get("item_id"), "vendor_id": lock.get("vendor_id")},
                {"$inc": {"reserved_qty": -int(item.get("qty", 0) or 0)}, "$set": {"updated_at": now}},
            )
        result = await db.resource_locks.update_one(
            {"id": lock.get("id"), "status": "ACTIVE"},
            {"$set": {"status": "EXPIRED", "released_at": now, "updated_at": now}},
        )
        if result.modified_count == 1:
            restored += 1
    return restored
