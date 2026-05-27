from __future__ import annotations

from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase


def _now() -> datetime:
    return datetime.now(timezone.utc)


class EscrowService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def capture_service_token(self, *, booking_id: str, vendor_id: str, amount: float, payment_id: str) -> None:
        now = _now()
        await self.db.be_escrow_ledger.insert_one(
            {
                "booking_id": booking_id,
                "vendor_id": vendor_id,
                "entry_type": "token_capture",
                "amount": round(float(amount), 2),
                "currency": "INR",
                "payment_id": payment_id,
                "status": "held",
                "created_at": now,
                "updated_at": now,
            }
        )

    async def mark_refund_pending(self, *, booking_id: str, reason: str) -> None:
        await self.db.be_escrow_ledger.update_many(
            {"booking_id": booking_id, "status": "held"},
            {
                "$set": {
                    "status": "refund_pending",
                    "refund_reason": reason,
                    "updated_at": _now(),
                }
            },
        )

    async def release_to_vendor(self, *, booking_id: str, released_by: str) -> None:
        await self.db.be_escrow_ledger.update_many(
            {"booking_id": booking_id, "status": "held"},
            {
                "$set": {
                    "status": "released",
                    "released_by": released_by,
                    "released_at": _now(),
                    "updated_at": _now(),
                }
            },
        )
