from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _daily_keys(start_iso: str, end_iso: str) -> List[str]:
    start = datetime.fromisoformat(start_iso.replace("Z", "+00:00")).date()
    end = datetime.fromisoformat(end_iso.replace("Z", "+00:00")).date()
    if end <= start:
        raise HTTPException(status_code=422, detail="rental_end must be after rental_start")
    keys: List[str] = []
    cursor = start
    while cursor < end:
        keys.append(cursor.isoformat())
        cursor = cursor + timedelta(days=1)
    return keys


class LockService:
    """Resource lock abstraction for slot, stock and rental window reservations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def lock_service_slot(
        self,
        *,
        intent_id: str,
        vendor_id: str,
        event_date: str,
        start_time: str,
        end_time: str,
        ttl_seconds: int,
    ) -> Dict[str, Any]:
        conflict = await self.db.be_locks.find_one(
            {
                "category": "service",
                "vendor_id": vendor_id,
                "event_date": event_date,
                "state": {"$in": ["soft_locked", "hard_locked"]},
                "start_time": {"$lt": end_time},
                "end_time": {"$gt": start_time},
            },
            {"_id": 0, "lock_key": 1},
        )
        if conflict:
            raise HTTPException(status_code=409, detail="Requested slot is no longer available")

        now = _utc_now()
        expires_at = now + timedelta(seconds=ttl_seconds)
        lock_key = f"service:{vendor_id}:{event_date}:{start_time}:{end_time}"
        doc = {
            "intent_id": intent_id,
            "lock_key": lock_key,
            "category": "service",
            "vendor_id": vendor_id,
            "event_date": event_date,
            "start_time": start_time,
            "end_time": end_time,
            "state": "soft_locked",
            "expires_at": expires_at,
            "created_at": now,
            "updated_at": now,
        }
        try:
            await self.db.be_locks.insert_one(doc)
        except Exception:
            raise HTTPException(status_code=409, detail="Requested slot is no longer available")

        return {"type": "service_slot", "lock_key": lock_key}

    async def lock_rental_inventory(
        self,
        *,
        intent_id: str,
        item_id: str,
        vendor_id: str,
        rental_start: str,
        rental_end: str,
        qty: int,
        ttl_seconds: int,
    ) -> Dict[str, Any]:
        day_keys = _daily_keys(rental_start, rental_end)
        reserved_days: List[str] = []

        base_item = await self.db.rental_inventory.find_one(
            {"id": item_id, "vendor_id": vendor_id, "is_active": True},
            {"_id": 0, "total_qty": 1},
        )
        if not base_item:
            raise HTTPException(status_code=404, detail="Rental item not found")

        for day in day_keys:
            await self.db.rental_inventory_windows.update_one(
                {"item_id": item_id, "day": day},
                {
                    "$setOnInsert": {
                        "item_id": item_id,
                        "vendor_id": vendor_id,
                        "day": day,
                        "available_qty": int(base_item.get("total_qty", 0)),
                        "created_at": _utc_now(),
                    }
                },
                upsert=True,
            )

            updated = await self.db.rental_inventory_windows.find_one_and_update(
                {"item_id": item_id, "day": day, "available_qty": {"$gte": qty}},
                {"$inc": {"available_qty": -qty}, "$set": {"updated_at": _utc_now()}},
                return_document=ReturnDocument.AFTER,
                projection={"_id": 0, "day": 1, "available_qty": 1},
            )
            if not updated:
                for reserved_day in reserved_days:
                    await self.db.rental_inventory_windows.update_one(
                        {"item_id": item_id, "day": reserved_day},
                        {"$inc": {"available_qty": qty}, "$set": {"updated_at": _utc_now()}},
                    )
                raise HTTPException(status_code=409, detail="Rental inventory not available for selected window")
            reserved_days.append(day)

        now = _utc_now()
        expires_at = now + timedelta(seconds=ttl_seconds)
        lock_key = f"rental:{item_id}:{rental_start}:{rental_end}:{intent_id}"
        await self.db.be_locks.insert_one(
            {
                "intent_id": intent_id,
                "lock_key": lock_key,
                "category": "rental",
                "vendor_id": vendor_id,
                "item_id": item_id,
                "rental_start": rental_start,
                "rental_end": rental_end,
                "qty": qty,
                "reserved_days": reserved_days,
                "state": "soft_locked",
                "expires_at": expires_at,
                "created_at": now,
                "updated_at": now,
            }
        )

        return {
            "type": "rental_inventory",
            "lock_key": lock_key,
            "item_id": item_id,
            "qty": qty,
            "reserved_days": reserved_days,
        }

    async def reserve_grocery_stock(self, *, intent_id: str, vendor_id: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        reservations: List[Dict[str, Any]] = []

        for item in items:
            item_id = item["item_id"]
            qty = int(item["qty"])
            updated = await self.db.grocery_catalog.find_one_and_update(
                {"id": item_id, "vendor_id": vendor_id, "stock_qty": {"$gte": qty}, "is_available": True},
                {"$inc": {"stock_qty": -qty}},
                return_document=ReturnDocument.AFTER,
                projection={"_id": 0, "id": 1, "stock_qty": 1},
            )
            if not updated:
                for reserved in reservations:
                    await self.db.grocery_catalog.update_one(
                        {"id": reserved["item_id"], "vendor_id": vendor_id},
                        {"$inc": {"stock_qty": reserved["qty"]}},
                    )
                raise HTTPException(status_code=409, detail=f"Insufficient stock for item {item_id}")
            reservations.append({"item_id": item_id, "qty": qty})

        await self.db.be_inventory_reservations.insert_one(
            {
                "intent_id": intent_id,
                "vendor_id": vendor_id,
                "category": "grocery",
                "items": reservations,
                "state": "reserved",
                "created_at": _utc_now(),
            }
        )
        return {"type": "grocery_stock", "vendor_id": vendor_id, "items": reservations}

    async def mark_reservation_committed(self, reservation: Dict[str, Any]) -> None:
        rtype = reservation.get("type")
        if rtype in {"service_slot", "rental_inventory"}:
            await self.db.be_locks.update_one(
                {"lock_key": reservation.get("lock_key"), "state": "soft_locked"},
                {"$set": {"state": "hard_locked", "updated_at": _utc_now()}},
            )
            return
        if rtype == "grocery_stock":
            await self.db.be_inventory_reservations.update_one(
                {"intent_id": reservation.get("intent_id")},
                {"$set": {"state": "committed", "updated_at": _utc_now()}},
            )

    async def release_reservation(self, reservation: Dict[str, Any]) -> None:
        rtype = reservation.get("type")

        if rtype == "service_slot":
            await self.db.be_locks.update_one(
                {"lock_key": reservation.get("lock_key")},
                {"$set": {"state": "released", "released_at": _utc_now(), "updated_at": _utc_now()}},
            )
            return

        if rtype == "rental_inventory":
            qty = int(reservation.get("qty", 0))
            item_id = reservation.get("item_id")
            for day in reservation.get("reserved_days", []):
                await self.db.rental_inventory_windows.update_one(
                    {"item_id": item_id, "day": day},
                    {"$inc": {"available_qty": qty}, "$set": {"updated_at": _utc_now()}},
                )
            await self.db.be_locks.update_one(
                {"lock_key": reservation.get("lock_key")},
                {"$set": {"state": "released", "released_at": _utc_now(), "updated_at": _utc_now()}},
            )
            return

        if rtype == "grocery_stock":
            for item in reservation.get("items", []):
                await self.db.grocery_catalog.update_one(
                    {"id": item["item_id"], "vendor_id": reservation.get("vendor_id")},
                    {"$inc": {"stock_qty": int(item["qty"])}, "$set": {"updated_at": _utc_now()}},
                )
            await self.db.be_inventory_reservations.update_one(
                {"intent_id": reservation.get("intent_id")},
                {"$set": {"state": "released", "updated_at": _utc_now()}},
            )
