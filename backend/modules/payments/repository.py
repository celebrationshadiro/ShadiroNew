from __future__ import annotations

from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase


class PaymentRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.orders.find_one({"id": order_id}, {"_id": 0})

    async def set_razorpay_order_id(self, order_id: str, razorpay_order_id: str, session=None) -> None:
        await self.db.orders.update_one(
            {"id": order_id},
            {"$set": {"razorpay_order_id": razorpay_order_id}},
            session=session,
        )

    async def find_payment_by_razorpay_payment_id(self, razorpay_payment_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.payments.find_one(
            {"razorpay_payment_id": razorpay_payment_id},
            {"_id": 0, "id": 1},
        )

    async def insert_payment(self, payment_doc: Dict[str, Any], session=None) -> None:
        await self.db.payments.insert_one(payment_doc, session=session)

    async def confirm_order_if_pending(self, order_id: str, payment_id: str, session=None):
        return await self.db.orders.update_one(
            {"id": order_id, "status": "pending"},
            {"$set": {"status": "confirmed", "payment_id": payment_id}},
            session=session,
        )

    async def update_order_commission_fields(self, order_id: str, update_payload: Dict[str, Any], session=None) -> None:
        await self.db.orders.update_one({"id": order_id}, {"$set": update_payload}, session=session)

    async def get_vendor(self, vendor_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.vendors.find_one({"id": vendor_id}, {"_id": 0})

    async def increment_vendor_payout_balance(self, vendor_id: str, amount: float, session=None) -> None:
        await self.db.vendors.update_one(
            {"id": vendor_id},
            {"$inc": {"vendor_payout_balance": amount}},
            session=session,
        )

    async def insert_vendor_ledger(self, ledger_doc: Dict[str, Any], session=None) -> None:
        await self.db.vendor_ledger.insert_one(ledger_doc, session=session)

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.users.find_one({"id": user_id}, {"_id": 0})

    async def insert_audit_log(self, log_doc: Dict[str, Any], session=None) -> None:
        try:
            await self.db.audit_logs.insert_one(log_doc, session=session)
        except Exception:
            # Never block payment flow due to audit insert.
            pass

    async def with_transaction(self, fn):
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                return await fn(session)
