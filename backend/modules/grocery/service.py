from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import HTTPException

from models import (
    AddressType,
    BookingContext,
    GroceryOrder,
    GroceryOrderCreate,
    GroceryOrderItem,
    GroceryOrderStatus,
    UserRole,
    VendorLedgerEntry,
    VendorType,
)
from services.commission_engine import build_commission_breakdown
from services.vendor_type import resolve_vendor_type

from .repository import GroceryRepository


class GroceryService:
    def __init__(self, repo: GroceryRepository):
        self.repo = repo

    def _normalize_delivery_address(self, address: dict) -> dict:
        if not address or not isinstance(address, dict):
            raise HTTPException(status_code=400, detail="Delivery address is required")

        required = ["name", "phone", "line1", "city", "state", "postal_code"]
        missing = [f for f in required if not str(address.get(f) or "").strip()]
        if missing:
            raise HTTPException(status_code=400, detail=f"Delivery address missing: {', '.join(missing)}")

        if not (address.get("instructions") or address.get("landmark")):
            raise HTTPException(status_code=400, detail="Add landmark or delivery instructions")

        normalized = {**address}
        normalized.setdefault("label", address.get("label") or address.get("name") or "Delivery")
        normalized.setdefault("address_type", AddressType.DELIVERY.value)
        if normalized.get("address_type") != AddressType.DELIVERY.value:
            raise HTTPException(status_code=400, detail="Delivery address must have address_type=delivery")
        normalized.setdefault("zone", address.get("city"))
        normalized.setdefault("is_default", address.get("is_default", False))
        return normalized

    async def create_order_with_stock_transaction(
        self,
        payload: GroceryOrderCreate,
        current_user: Dict[str, Any],
    ) -> GroceryOrder:
        if current_user.get("role") != UserRole.CUSTOMER:
            raise HTTPException(status_code=403, detail="Only users can place grocery orders")

        ctx = (
            payload.booking_context.value
            if hasattr(payload.booking_context, "value")
            else str(payload.booking_context or "")
        ).upper()
        if ctx and ctx != BookingContext.GROCERY.value:
            raise HTTPException(status_code=400, detail="Use grocery checkout for delivery orders")

        vendor = await self.repo.get_vendor(payload.vendor_id)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        if resolve_vendor_type(vendor.get("category_id"), vendor.get("vendor_type")) != VendorType.PRODUCT_VENDOR:
            raise HTTPException(status_code=400, detail="This vendor does not support grocery checkout")

        if not payload.items:
            raise HTTPException(status_code=400, detail="No items selected")

        address_dict = self._normalize_delivery_address(
            payload.delivery_address.model_dump()
            if hasattr(payload.delivery_address, "model_dump")
            else dict(payload.delivery_address)
        )
        delivery_zone = address_dict.get("zone") or address_dict.get("city")

        item_ids = [i.item_id for i in payload.items]
        items_db = await self.repo.get_items_by_ids(payload.vendor_id, item_ids)
        items_map = {i["id"]: i for i in items_db}

        normalized_items: List[GroceryOrderItem] = []
        total_amount = 0.0
        for item in payload.items:
            if item.item_id not in items_map:
                raise HTTPException(status_code=400, detail="Invalid item selection")
            db_item = items_map[item.item_id]
            qty = max(int(item.qty or 1), 1)
            unit_price = float(db_item.get("unit_price") or 0)
            total_price = unit_price * qty
            total_amount += total_price
            normalized_items.append(
                GroceryOrderItem(
                    item_id=item.item_id,
                    name=db_item.get("name"),
                    qty=qty,
                    unit_price=unit_price,
                    unit=db_item.get("unit") or "item",
                    total_price=total_price,
                )
            )

        serviceability_warning = None
        service_areas = vendor.get("service_areas") or []
        if service_areas and delivery_zone:
            allowed = {str(a).lower() for a in service_areas}
            if str(delivery_zone).lower() not in allowed:
                raise HTTPException(status_code=400, detail="Address is outside vendor service area")
        elif vendor.get("city") and delivery_zone:
            if str(vendor.get("city")).lower() != str(delivery_zone).lower():
                serviceability_warning = "city_mismatch"

        order_doc = GroceryOrder(
            user_id=current_user.get("sub"),
            vendor_id=payload.vendor_id,
            items=normalized_items,
            delivery_address=address_dict,
            delivery_eta=payload.delivery_eta,
            total_amount=total_amount,
            booking_context=BookingContext.GROCERY,
            delivery_zone=delivery_zone,
            serviceability_warning=serviceability_warning,
            ai_context_address=address_dict,
        ).model_dump()
        order_doc["created_at"] = order_doc["created_at"].isoformat()

        async def _txn(session):
            now_iso = datetime.now(timezone.utc).isoformat()
            for item in normalized_items:
                stock_update = await self.repo.decrement_stock_if_available(
                    item.item_id, item.qty, now_iso, session=session
                )
                if stock_update.modified_count != 1:
                    raise HTTPException(status_code=400, detail=f"Insufficient stock for {item.name}")
            await self.repo.insert_grocery_order(order_doc, session=session)

        await self.repo.with_transaction(_txn)
        return GroceryOrder(**order_doc)

    async def update_order_status_with_transaction(
        self,
        order_id: str,
        new_status: GroceryOrderStatus,
        current_user: Dict[str, Any],
    ) -> Dict[str, Any]:
        order = await self.repo.get_grocery_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        role = current_user.get("role")
        if role == UserRole.CUSTOMER:
            if order.get("user_id") != current_user.get("sub"):
                raise HTTPException(status_code=403, detail="Not allowed")
            if new_status != GroceryOrderStatus.CANCELLED:
                raise HTTPException(status_code=400, detail="Users can only cancel orders")
            if order.get("status") not in (GroceryOrderStatus.PLACED, GroceryOrderStatus.PACKED):
                raise HTTPException(status_code=400, detail="Order can no longer be cancelled")
        elif role == UserRole.VENDOR:
            vendor = await self.repo.get_vendor_by_user(current_user.get("sub"))
            if not vendor or order.get("vendor_id") != vendor.get("id"):
                raise HTTPException(status_code=403, detail="Not allowed")
            if resolve_vendor_type(vendor.get("category_id"), vendor.get("vendor_type")) != VendorType.PRODUCT_VENDOR:
                raise HTTPException(status_code=400, detail="Only grocery vendors can update grocery orders")
        else:
            raise HTTPException(status_code=403, detail="Not allowed")

        old_status = order.get("status")
        now_iso = datetime.now(timezone.utc).isoformat()

        async def _txn(session):
            await self.repo.update_grocery_order(
                order_id,
                {"status": new_status, "updated_at": now_iso},
                session=session,
            )
            await self.repo.insert_audit_log(
                action_type="order_status_change",
                performed_by=role if role else "system",
                performed_by_id=current_user.get("sub"),
                entity_type="grocery_order",
                entity_id=order_id,
                old_value={"status": old_status},
                new_value={"status": new_status},
                session=session,
            )

            if new_status == GroceryOrderStatus.DELIVERED:
                vendor_doc = await self.repo.get_vendor(order.get("vendor_id"))
                if vendor_doc:
                    existing_ledger = await self.repo.get_vendor_ledger_for_grocery_order(order_id)
                    if not existing_ledger:
                        breakdown = build_commission_breakdown(vendor_doc, float(order.get("total_amount") or 0))
                        commission_amount = breakdown["commission_amount"]
                        net_amount = breakdown["net_amount"]
                        gateway_fee = breakdown["gateway_fee"]

                        await self.repo.increment_vendor_payout_balance(
                            vendor_doc.get("id"),
                            net_amount,
                            session=session,
                        )
                        await self.repo.update_grocery_order(
                            order_id,
                            {
                                "commission_percentage": breakdown["commission_percentage"],
                                "minimum_commission": breakdown["minimum_commission"],
                                "commission_amount": commission_amount,
                                "vendor_payout_amount": net_amount,
                                "gateway_fee": gateway_fee,
                            },
                            session=session,
                        )

                        ledger_entry = VendorLedgerEntry(
                            vendor_id=vendor_doc.get("id"),
                            order_id=order_id,
                            source_type="grocery_order",
                            gross_amount=float(order.get("total_amount") or 0),
                            commission_percentage=breakdown["commission_percentage"],
                            minimum_commission=breakdown["minimum_commission"],
                            commission_amount=commission_amount,
                            net_amount=net_amount,
                            gateway_fee=gateway_fee,
                        ).model_dump()
                        ledger_entry["created_at"] = ledger_entry["created_at"].isoformat()
                        await self.repo.insert_vendor_ledger(ledger_entry, session=session)

        await self.repo.with_transaction(_txn)
        updated = await self.repo.get_grocery_order(order_id)
        return {"status": "success", "order": updated}
