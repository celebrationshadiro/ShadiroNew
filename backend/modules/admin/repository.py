from __future__ import annotations

from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase


class AdminRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def insert_admin_audit_log(self, log_doc: Dict[str, Any], session=None) -> None:
        await self.db.admin_audit_logs.insert_one(log_doc, session=session)

    async def count_users(self) -> int:
        return await self.db.users.count_documents({})

    async def count_vendors(self) -> int:
        return await self.db.vendors.count_documents({})

    async def count_pending_vendors(self) -> int:
        return await self.db.vendors.count_documents({"status": "pending"})

    async def list_confirmed_paid_orders(self, limit: int) -> List[Dict[str, Any]]:
        return await self.db.orders.find(
            {"status": "confirmed", "payment_id": {"$exists": True, "$ne": None}},
            {"_id": 0, "total_amount": 1},
        ).to_list(limit)

    async def list_confirmed_orders_since(self, created_at_gte: str, limit: int) -> List[Dict[str, Any]]:
        return await self.db.orders.find(
            {"status": "confirmed", "created_at": {"$gte": created_at_gte}},
            {"_id": 0, "created_at": 1},
        ).to_list(limit)

    async def list_approved_vendor_categories(self, limit: int) -> List[Dict[str, Any]]:
        return await self.db.vendors.find(
            {"status": "approved"}, {"_id": 0, "category_id": 1}
        ).to_list(limit)

    async def list_vendor_categories(self, limit: int) -> List[Dict[str, Any]]:
        return await self.db.vendor_categories.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(limit)

    async def list_vendors_for_pricing(self, limit: int) -> List[Dict[str, Any]]:
        return await self.db.vendors.find(
            {}, {"_id": 0, "base_price": 1, "pricing_rules": 1, "category_id": 1}
        ).to_list(limit)

    async def list_users(self, query: Dict[str, Any], skip: int, limit: int) -> List[Dict[str, Any]]:
        cursor = self.db.users.find(query, {"_id": 0, "hashed_password": 0}).skip(skip).limit(limit)
        return await cursor.to_list(limit)

    async def list_vendors(self, query: Dict[str, Any], skip: int, limit: int) -> List[Dict[str, Any]]:
        cursor = self.db.vendors.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(limit)

    async def get_vendor(self, vendor_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.vendors.find_one({"id": vendor_id}, {"_id": 0})

    async def update_vendor_fields(self, vendor_id: str, update_data: Dict[str, Any]) -> None:
        await self.db.vendors.update_one({"id": vendor_id}, {"$set": update_data})

    async def get_vendor_commission_fields(self, vendor_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.vendors.find_one(
            {"id": vendor_id}, {"_id": 0, "commission_percentage": 1, "minimum_commission": 1}
        )

    async def list_vendor_ledger(self, limit: int) -> List[Dict[str, Any]]:
        return await self.db.vendor_ledger.find({}, {"_id": 0}).to_list(limit)

    async def list_vendors_by_ids(self, vendor_ids: List[str]) -> List[Dict[str, Any]]:
        if not vendor_ids:
            return []
        return await self.db.vendors.find(
            {"id": {"$in": vendor_ids}}, {"_id": 0, "id": 1, "category_id": 1}
        ).to_list(len(vendor_ids))

    async def list_pending_payout_vendors(self, limit: int) -> List[Dict[str, Any]]:
        return await self.db.vendors.find(
            {"vendor_payout_balance": {"$gt": 0}},
            {"_id": 0, "id": 1, "business_name": 1, "vendor_payout_balance": 1, "category_id": 1},
        ).sort("vendor_payout_balance", -1).to_list(limit)

    async def list_payout_requests(self, skip: int, limit: int) -> List[Dict[str, Any]]:
        return await self.db.vendor_payouts.find({}, {"_id": 0}).sort("requested_at", -1).skip(skip).limit(limit).to_list(limit)

    async def get_payout(self, payout_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.vendor_payouts.find_one({"id": payout_id}, {"_id": 0})

    async def complete_payout_if_pending(self, payout_id: str, admin_id: str, now: str):
        return await self.db.vendor_payouts.update_one(
            {"id": payout_id, "status": "pending"},
            {"$set": {"status": "completed", "payout_date": now, "admin_id": admin_id}},
        )

    async def reset_payout_to_pending(self, payout_id: str) -> None:
        await self.db.vendor_payouts.update_one(
            {"id": payout_id}, {"$set": {"status": "pending", "payout_date": None, "admin_id": None}}
        )

    async def decrement_vendor_payout_balance(self, vendor_id: str, amount: float):
        return await self.db.vendors.update_one(
            {"id": vendor_id, "vendor_payout_balance": {"$gte": amount}},
            {"$inc": {"vendor_payout_balance": -amount, "withdrawn_amount": amount}},
        )

    async def get_vendor_ledger_by_payout(self, payout_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.vendor_ledger.find_one({"payout_id": payout_id}, {"_id": 0, "id": 1})

    async def insert_vendor_ledger(self, ledger_doc: Dict[str, Any]) -> None:
        await self.db.vendor_ledger.insert_one(ledger_doc)

    async def reject_payout_if_pending(self, payout_id: str, admin_id: str, admin_note: Optional[str]):
        return await self.db.vendor_payouts.update_one(
            {"id": payout_id, "status": "pending"},
            {"$set": {"status": "rejected", "admin_id": admin_id, "admin_note": admin_note}},
        )

    async def insert_settlement(self, settlement: Dict[str, Any]) -> None:
        await self.db.settlements.insert_one(settlement)

    async def get_settlement(self, settlement_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.settlements.find_one({"id": settlement_id}, {"_id": 0})

    async def mark_settlement_paid(self, settlement_id: str, paid_at: str, paid_by: str) -> None:
        await self.db.settlements.update_one(
            {"id": settlement_id},
            {"$set": {"status": "paid", "paid_at": paid_at, "paid_by": paid_by}},
        )

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.users.find_one({"id": user_id}, {"_id": 0})

    async def update_vendor_approval_action(self, vendor_id: str, update_data: Dict[str, Any], session=None) -> None:
        await self.db.vendors.update_one({"id": vendor_id}, {"$set": update_data}, session=session)

    async def set_vendor_featured(self, vendor_id: str, featured: bool, updated_at: str):
        return await self.db.vendors.update_one(
            {"id": vendor_id}, {"$set": {"is_featured": featured, "updated_at": updated_at}}
        )

    async def set_vendor_verified(self, vendor_id: str, updated_at: str):
        return await self.db.vendors.update_one(
            {"id": vendor_id},
            {"$set": {"is_verified": True, "verification_status": "approved", "updated_at": updated_at}},
        )

    async def list_orders(self, query: Dict[str, Any], skip: int, limit: int) -> List[Dict[str, Any]]:
        cursor = self.db.orders.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(limit)

    async def list_payments(self, skip: int, limit: int) -> List[Dict[str, Any]]:
        cursor = self.db.payments.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(limit)

    async def block_user(self, user_id: str, reason: str, blocked_at: str):
        return await self.db.users.update_one(
            {"id": user_id},
            {"$set": {"is_active": False, "blocked_at": blocked_at, "block_reason": reason}},
        )

    async def activate_user(self, user_id: str):
        return await self.db.users.update_one({"id": user_id}, {"$set": {"is_active": True}})

    async def list_admin_audit_logs(self, query: Dict[str, Any], skip: int, limit: int) -> List[Dict[str, Any]]:
        cursor = self.db.admin_audit_logs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(limit)

    async def list_platform_audit_logs(self, query: Dict[str, Any], skip: int, limit: int) -> List[Dict[str, Any]]:
        cursor = self.db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit)
        return await cursor.to_list(limit)

    async def count_vendor_orders(self, vendor_id: str) -> int:
        return await self.db.orders.count_documents({"vendor_id": vendor_id})

    async def count_vendor_confirmed_orders(self, vendor_id: str) -> int:
        return await self.db.orders.count_documents({"vendor_id": vendor_id, "status": "confirmed"})

    async def list_vendor_confirmed_order_amounts(self, vendor_id: str, limit: int) -> List[Dict[str, Any]]:
        return await self.db.orders.find(
            {"vendor_id": vendor_id, "status": "confirmed"}, {"_id": 0, "total_amount": 1}
        ).to_list(limit)

    async def list_vendor_reviews(self, vendor_id: str, limit: int) -> List[Dict[str, Any]]:
        return await self.db.reviews.find({"vendor_id": vendor_id}, {"_id": 0, "rating": 1}).to_list(limit)

    async def list_vendor_reliability(self, skip: int, limit: int) -> List[Dict[str, Any]]:
        return await self.db.vendors.find(
            {},
            {
                "_id": 0,
                "id": 1,
                "business_name": 1,
                "city": 1,
                "accepted_count": 1,
                "rejected_count": 1,
                "completed_count": 1,
                "emergency_count": 1,
                "acceptance_rate": 1,
            },
        ).skip(skip).limit(limit).to_list(limit)

    async def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.payments.find_one({"id": payment_id}, {"_id": 0})

    async def mark_payment_refunded(self, payment_id: str, refund_id: str, reason: str, refunded_at: str) -> None:
        await self.db.payments.update_one(
            {"id": payment_id},
            {
                "$set": {
                    "status": "refunded",
                    "refund_id": refund_id,
                    "refund_reason": reason,
                    "refunded_at": refunded_at,
                }
            },
        )

    async def with_transaction(self, fn):
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                return await fn(session)
