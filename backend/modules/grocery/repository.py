from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase


class GroceryRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_vendor(self, vendor_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.vendors.find_one(
            {"id": vendor_id},
            {"_id": 0, "id": 1, "category_id": 1, "vendor_type": 1, "service_areas": 1, "city": 1, "details": 1},
        )

    async def get_vendor_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.vendors.find_one(
            {"user_id": user_id},
            {"_id": 0, "id": 1, "category_id": 1, "vendor_type": 1},
        )

    async def get_items_by_ids(self, vendor_id: str, item_ids: List[str]) -> List[Dict[str, Any]]:
        return await self.db.grocery_items.find(
            {"id": {"$in": item_ids}, "vendor_id": vendor_id},
            {"_id": 0},
        ).to_list(500)

    async def decrement_stock_if_available(self, item_id: str, qty: int, updated_at: str, session=None):
        return await self.db.grocery_items.update_one(
            {"id": item_id, "stock_qty": {"$gte": qty}},
            {"$inc": {"stock_qty": -qty}, "$set": {"updated_at": updated_at}},
            session=session,
        )

    async def insert_grocery_order(self, order_doc: Dict[str, Any], session=None) -> None:
        await self.db.grocery_orders.insert_one(order_doc, session=session)

    async def get_grocery_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.grocery_orders.find_one({"id": order_id}, {"_id": 0})

    async def update_grocery_order(self, order_id: str, update_data: Dict[str, Any], session=None):
        return await self.db.grocery_orders.update_one(
            {"id": order_id},
            {"$set": update_data},
            session=session,
        )

    async def get_vendor_ledger_for_grocery_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.vendor_ledger.find_one(
            {"order_id": order_id, "source_type": "grocery_order"},
            {"_id": 0, "id": 1},
        )

    async def increment_vendor_payout_balance(self, vendor_id: str, amount: float, session=None) -> None:
        await self.db.vendors.update_one(
            {"id": vendor_id},
            {"$inc": {"vendor_payout_balance": amount}},
            session=session,
        )

    async def insert_vendor_ledger(self, ledger_doc: Dict[str, Any], session=None) -> None:
        await self.db.vendor_ledger.insert_one(ledger_doc, session=session)

    async def insert_audit_log(
        self,
        action_type: str,
        performed_by: str,
        performed_by_id: Optional[str],
        entity_type: str,
        entity_id: str,
        old_value: Dict[str, Any],
        new_value: Dict[str, Any],
        session=None,
    ) -> None:
        log_doc = {
            "id": str(uuid.uuid4()),
            "action_type": action_type,
            "performed_by": performed_by,
            "performed_by_id": performed_by_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "old_value": old_value,
            "new_value": new_value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            await self.db.audit_logs.insert_one(log_doc, session=session)
        except Exception:
            pass

    async def with_transaction(self, fn):
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                return await fn(session)
