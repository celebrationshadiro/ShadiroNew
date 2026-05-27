from __future__ import annotations

from typing import Any, Dict

from fastapi import HTTPException

from booking_engine.lock_service import acquire_date_range_lock, release_lock
from booking_engine.handlers.base_handler import BaseBookingHandler
from booking_engine.models.booking_models import CategoryType


class RentalBookingHandler(BaseBookingHandler):
    category_type = CategoryType.RENTAL

    async def validate_create(self, payload: Dict[str, Any], current_user: Dict[str, Any]) -> None:
        vendor = await self.db.vendors.find_one(
            {"id": payload["vendor_id"], "is_active": True},
            {"_id": 0, "id": 1},
        )
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not available")

        item = await self.db.rental_inventory.find_one(
            {"id": payload["inventory_item_id"], "vendor_id": payload["vendor_id"], "is_active": True},
            {"_id": 0, "id": 1, "total_qty": 1},
        )
        if not item:
            raise HTTPException(status_code=404, detail="Rental item not available")
        if int(payload["qty"]) > int(item.get("total_qty", 0)):
            raise HTTPException(status_code=422, detail="Requested quantity exceeds available inventory")

    async def reserve_resources(self, payload: Dict[str, Any], intent_id: str, ttl_seconds: int) -> Dict[str, Any]:
        _ = ttl_seconds
        lock_result = await acquire_date_range_lock(
            self.db,
            item_id=payload["inventory_item_id"],
            check_in=payload["rental_start"].split("T")[0],
            check_out=payload["rental_end"].split("T")[0],
            intent_id=intent_id,
            ttl_min=20,
        )
        return {
            "type": "rental_date_range",
            "lock_id": lock_result["lock_id"],
            "days": lock_result["days"],
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
        rental_amount = round(float(payload["rental_amount"]), 2)
        deposit_amount = round(float(payload.get("deposit_amount", 0)), 2)
        required_deposit = round(max(rental_amount * 0.3, 0), 2)
        payable_now = required_deposit
        balance_due = round(max(rental_amount - required_deposit, 0), 2)
        return {
            "currency": "INR",
            "payable_now": payable_now,
            "advance_rental": required_deposit,
            "deposit_amount": deposit_amount,
            "deposit_percent": 30,
            "balance_due": balance_due,
            "rental_amount": rental_amount,
            "total_amount": round(rental_amount + deposit_amount, 2),
            "settlement_mode": "deposit_hold",
        }
