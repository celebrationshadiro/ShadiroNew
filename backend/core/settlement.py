from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from canonical_models.common import LedgerEntryType, PayoutStatus, utcnow


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


@dataclass
class CommissionBreakdown:
    gross_paise: int
    commission_rate_bps: int
    commission_amount_paise: int
    vendor_net_paise: int


class SettlementService:
    """
    Canonical settlement service:
    - commission resolution
    - booking settlement ledger entries
    - payout lifecycle (PENDING -> APPROVED -> PROCESSED)
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    @staticmethod
    def _validate_non_negative_amount(value: int, field_name: str) -> None:
        if not isinstance(value, int):
            raise HTTPException(status_code=400, detail=f"{field_name} must be an integer paise amount")
        if value < 0:
            raise HTTPException(status_code=400, detail=f"{field_name} cannot be negative")

    async def get_commission_rate(self, vendor_id: str, category_type: str) -> int:
        """
        Returns commission rate in basis points.
        Priority:
          1) vendors.commission_override_bps
          2) vendor_categories.default_commission_bps for category
          3) platform_config.default_commission_bps
          4) hard default 10% (1000 bps)
        """
        vendor = await self.db.vendors.find_one(
            {"id": vendor_id},
            {"_id": 0, "commission_override_bps": 1, "category_id": 1},
        )
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

        override = vendor.get("commission_override_bps")
        if isinstance(override, int) and 0 <= override <= 10000:
            return override

        category_id = vendor.get("category_id")
        if category_id:
            category_doc = await self.db.vendor_categories.find_one(
                {"id": category_id},
                {"_id": 0, "default_commission_bps": 1},
            )
            category_bps = (category_doc or {}).get("default_commission_bps")
            if isinstance(category_bps, int) and 0 <= category_bps <= 10000:
                return category_bps

        config_doc = await self.db.platform_config.find_one(
            {"key": "commission_defaults"},
            {"_id": 0, "default_commission_bps": 1},
        )
        config_bps = (config_doc or {}).get("default_commission_bps")
        if isinstance(config_bps, int) and 0 <= config_bps <= 10000:
            return config_bps

        _ = category_type  # reserved for future category-type overrides
        return 1000  # 10%

    async def calculate_and_record(self, booking_id: str) -> dict[str, Any]:
        """
        Computes settlement for a completed booking and writes:
        - booking financial snapshot
        - ledger CREDIT entry
        - ledger HOLD entry (held until payout processing)
        """
        booking = await self.db.bookings.find_one({"id": booking_id}, {"_id": 0})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.get("status") != "COMPLETED":
            raise HTTPException(status_code=409, detail="Settlement requires COMPLETED booking")
        if booking.get("settlement_status") == "SETTLED":
            return {
                "gross": int(booking.get("amount_gross_paise", 0)),
                "commission_amount": int(booking.get("commission_amount_paise", 0)),
                "vendor_net": int(booking.get("vendor_net_paise", 0)),
                "already_settled": True,
            }

        gross_paise = int(booking.get("amount_gross_paise") or 0)
        self._validate_non_negative_amount(gross_paise, "amount_gross_paise")

        rate_bps = await self.get_commission_rate(
            vendor_id=booking["vendor_id"],
            category_type=booking.get("category_type", "service"),
        )
        commission_paise = (gross_paise * rate_bps) // 10000
        vendor_net_paise = gross_paise - commission_paise
        self._validate_non_negative_amount(vendor_net_paise, "vendor_net_paise")

        breakdown = CommissionBreakdown(
            gross_paise=gross_paise,
            commission_rate_bps=rate_bps,
            commission_amount_paise=commission_paise,
            vendor_net_paise=vendor_net_paise,
        )

        async def _txn(session):
            now = utcnow()
            update_result = await self.db.bookings.update_one(
                {"id": booking_id, "version": int(booking.get("version", 1))},
                {
                    "$set": {
                        "commission_rate_bps": breakdown.commission_rate_bps,
                        "commission_amount_paise": breakdown.commission_amount_paise,
                        "vendor_net_paise": breakdown.vendor_net_paise,
                        "settlement_status": "SETTLED",
                        "updated_at": now,
                    },
                    "$inc": {"version": 1},
                },
                session=session,
            )
            if update_result.modified_count != 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Conflict while writing booking settlement snapshot",
                )

            await self.credit_vendor_ledger(
                vendor_id=booking["vendor_id"],
                amount_paise=breakdown.vendor_net_paise,
                booking_id=booking_id,
                note="Booking completion credit",
                entry_type=LedgerEntryType.CREDIT,
                session=session,
            )
            await self.credit_vendor_ledger(
                vendor_id=booking["vendor_id"],
                amount_paise=breakdown.vendor_net_paise,
                booking_id=booking_id,
                note="Hold until payout approval",
                entry_type=LedgerEntryType.HOLD,
                session=session,
            )

            await self.db.platform_revenue.insert_one(
                {
                    "id": _new_id("rev"),
                    "booking_id": booking_id,
                    "vendor_id": booking["vendor_id"],
                    "commission_rate_bps": breakdown.commission_rate_bps,
                    "commission_amount_paise": breakdown.commission_amount_paise,
                    "created_at": now,
                },
                session=session,
            )

        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                await _txn(session)

        return {
            "gross": breakdown.gross_paise,
            "commission_amount": breakdown.commission_amount_paise,
            "vendor_net": breakdown.vendor_net_paise,
            "already_settled": False,
        }

    async def credit_vendor_ledger(
        self,
        vendor_id: str,
        amount_paise: int,
        booking_id: str,
        note: str,
        entry_type: LedgerEntryType = LedgerEntryType.CREDIT,
        session=None,
    ) -> dict[str, Any]:
        self._validate_non_negative_amount(amount_paise, "amount_paise")
        now = utcnow()

        vendor = await self.db.vendors.find_one({"id": vendor_id}, {"_id": 0, "id": 1}, session=session)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

        # Wallet behavior:
        # - CREDIT: available += amount
        # - HOLD: available -= amount, hold += amount
        # - RELEASE: hold -= amount
        if entry_type == LedgerEntryType.CREDIT:
            inc_doc = {"wallet_available_paise": amount_paise}
        elif entry_type == LedgerEntryType.HOLD:
            inc_doc = {"wallet_available_paise": -amount_paise, "wallet_hold_paise": amount_paise}
        elif entry_type == LedgerEntryType.RELEASE:
            inc_doc = {"wallet_hold_paise": -amount_paise}
        elif entry_type == LedgerEntryType.DEBIT:
            inc_doc = {"wallet_available_paise": -amount_paise}
        else:
            inc_doc = {}

        updated_vendor = await self.db.vendors.find_one_and_update(
            {"id": vendor_id},
            {"$inc": inc_doc, "$set": {"updated_at": now}},
            return_document=ReturnDocument.AFTER,
            projection={"_id": 0, "wallet_available_paise": 1, "wallet_hold_paise": 1},
            session=session,
        )
        balance_after = int(updated_vendor.get("wallet_available_paise", 0)) if updated_vendor else 0

        ledger_entry = {
            "id": _new_id("led"),
            "vendor_id": vendor_id,
            "booking_id": booking_id,
            "entry_type": entry_type.value,
            "amount_paise": amount_paise,
            "balance_after_paise": balance_after,
            "note": note,
            "created_at": now,
        }
        await self.db.vendor_ledger.insert_one(ledger_entry, session=session)
        return ledger_entry

    async def create_payout_request(self, vendor_id: str) -> dict[str, Any]:
        vendor = await self.db.vendors.find_one(
            {"id": vendor_id},
            {"_id": 0, "wallet_hold_paise": 1},
        )
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

        hold_paise = int(vendor.get("wallet_hold_paise", 0) or 0)
        if hold_paise <= 0:
            raise HTTPException(status_code=400, detail="No held balance available for payout")

        existing_pending = await self.db.payouts.find_one(
            {"vendor_id": vendor_id, "status": PayoutStatus.PENDING.value},
            {"_id": 0, "id": 1},
        )
        if existing_pending:
            raise HTTPException(status_code=409, detail="A pending payout request already exists")

        now = utcnow()
        payout = {
            "id": _new_id("po"),
            "vendor_id": vendor_id,
            "amount_paise": hold_paise,
            "status": PayoutStatus.PENDING.value,
            "created_at": now,
            "updated_at": now,
            "approved_at": None,
            "processed_at": None,
            "approved_by": None,
            "processed_by": None,
            "note": "Payout requested by vendor",
        }
        await self.db.payouts.insert_one(payout)
        return payout

    async def admin_approve_payout(self, payout_id: str, admin_id: str) -> dict[str, Any]:
        payout = await self.db.payouts.find_one({"id": payout_id}, {"_id": 0})
        if not payout:
            raise HTTPException(status_code=404, detail="Payout request not found")
        if payout.get("status") != PayoutStatus.PENDING.value:
            raise HTTPException(status_code=409, detail="Payout is not in PENDING state")

        approved = await self.db.payouts.find_one_and_update(
            {"id": payout_id, "status": PayoutStatus.PENDING.value},
            {
                "$set": {
                    "status": PayoutStatus.APPROVED.value,
                    "approved_by": admin_id,
                    "approved_at": utcnow(),
                    "updated_at": utcnow(),
                }
            },
            return_document=ReturnDocument.AFTER,
            projection={"_id": 0},
        )
        if not approved:
            raise HTTPException(status_code=409, detail="Payout state conflict on approval")
        return approved
