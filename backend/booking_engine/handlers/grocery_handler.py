from __future__ import annotations

from typing import Any, Dict

from fastapi import HTTPException

from booking_engine.lock_service import acquire_stock_lock, release_lock
from booking_engine.handlers.base_handler import BaseBookingHandler
from booking_engine.models.booking_models import CategoryType


class GroceryBookingHandler(BaseBookingHandler):
    category_type = CategoryType.GROCERY

    async def validate_create(self, payload: Dict[str, Any], current_user: Dict[str, Any]) -> None:
        vendor = await self.db.vendors.find_one(
            {"id": payload["vendor_id"], "is_active": True},
            {"_id": 0, "id": 1},
        )
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not available")
        if not payload.get("delivery_address"):
            raise HTTPException(status_code=422, detail="delivery_address is required")
        if not payload.get("items"):
            raise HTTPException(status_code=422, detail="items are required")
        if float(payload.get("payment_amount") or 0) <= 0:
            raise HTTPException(status_code=422, detail="payment_amount must be greater than zero")

    async def reserve_resources(self, payload: Dict[str, Any], intent_id: str, ttl_seconds: int) -> Dict[str, Any]:
        _ = ttl_seconds
        lock_result = await acquire_stock_lock(
            self.db,
            vendor_id=payload["vendor_id"],
            items=[{"item_id": i["item_id"], "qty": i["qty"]} for i in payload["items"]],
            intent_id=intent_id,
            ttl_min=15,
        )
        return {
            "type": "grocery_stock",
            "lock_id": lock_result["lock_id"],
            "items": lock_result["items"],
            "expires_at": lock_result["expires_at"],
        }

    async def release_resources(self, reservation: Dict[str, Any]) -> None:
        lock_id = str(reservation.get("lock_id") or "")
        if lock_id:
            await release_lock(self.db, lock_id)

    def requires_vendor_acceptance(self) -> bool:
        return False

    def uses_escrow(self) -> bool:
        return False

    def payment_summary(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        payable = round(float(payload["payment_amount"]), 2)
        return {
            "currency": "INR",
            "payable_now": payable,
            "total_amount": payable,
            "settlement_mode": "direct",
        }
