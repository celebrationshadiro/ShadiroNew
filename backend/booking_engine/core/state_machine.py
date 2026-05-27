from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Set

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from booking_engine.models.booking_models import ActorRole, BookingStatus, CategoryType


BASE_TRANSITIONS: Dict[BookingStatus, Set[BookingStatus]] = {
    BookingStatus.INTENT_CREATED: {BookingStatus.AWAITING_PAYMENT, BookingStatus.EXPIRED},
    BookingStatus.AWAITING_PAYMENT: {BookingStatus.PAYMENT_PENDING_VERIFICATION, BookingStatus.CANCELLED, BookingStatus.EXPIRED},
    BookingStatus.PAYMENT_PENDING_VERIFICATION: {BookingStatus.TOKEN_PAID, BookingStatus.CANCELLED, BookingStatus.REFUND_PENDING},
    BookingStatus.TOKEN_PAID: {BookingStatus.VENDOR_PENDING, BookingStatus.CONFIRMED, BookingStatus.REFUND_PENDING},
    BookingStatus.VENDOR_PENDING: {
        BookingStatus.VENDOR_ACCEPTED,
        BookingStatus.VENDOR_COUNTERED,
        BookingStatus.VENDOR_REJECTED,
        BookingStatus.EXPIRED,
        BookingStatus.CANCELLED,
    },
    BookingStatus.VENDOR_COUNTERED: {BookingStatus.VENDOR_ACCEPTED, BookingStatus.CANCELLED, BookingStatus.EXPIRED},
    BookingStatus.VENDOR_ACCEPTED: {BookingStatus.CONFIRMED, BookingStatus.CANCELLED},
    BookingStatus.CONFIRMED: {BookingStatus.IN_PROGRESS, BookingStatus.CANCELLED},
    BookingStatus.IN_PROGRESS: {BookingStatus.COMPLETED, BookingStatus.CANCELLED},
    BookingStatus.COMPLETED: {BookingStatus.PAYOUT_PENDING, BookingStatus.PAYOUT_RELEASED},
    BookingStatus.PAYOUT_PENDING: {BookingStatus.PAYOUT_RELEASED},
    BookingStatus.VENDOR_REJECTED: {BookingStatus.REFUND_PENDING},
    BookingStatus.CANCELLED: {BookingStatus.REFUND_PENDING},
    BookingStatus.REFUND_PENDING: {BookingStatus.REFUNDED},
    BookingStatus.REFUNDED: set(),
    BookingStatus.PAYOUT_RELEASED: set(),
    BookingStatus.EXPIRED: {BookingStatus.REFUND_PENDING},
}


CATEGORY_OVERRIDES: Dict[CategoryType, Dict[BookingStatus, Set[BookingStatus]]] = {
    CategoryType.GROCERY: {
        BookingStatus.TOKEN_PAID: {BookingStatus.CONFIRMED},
        BookingStatus.CONFIRMED: {BookingStatus.IN_PROGRESS, BookingStatus.COMPLETED, BookingStatus.CANCELLED},
        BookingStatus.COMPLETED: {BookingStatus.PAYOUT_RELEASED},
    },
    CategoryType.SERVICE: {
        BookingStatus.TOKEN_PAID: {BookingStatus.VENDOR_PENDING},
        BookingStatus.VENDOR_ACCEPTED: {BookingStatus.CONFIRMED},
        BookingStatus.COMPLETED: {BookingStatus.PAYOUT_PENDING},
    },
    CategoryType.RENTAL: {
        BookingStatus.TOKEN_PAID: {BookingStatus.VENDOR_PENDING},
        BookingStatus.VENDOR_ACCEPTED: {BookingStatus.CONFIRMED},
        BookingStatus.COMPLETED: {BookingStatus.PAYOUT_RELEASED},
    },
}


ROLE_GUARDS: Dict[BookingStatus, Set[ActorRole]] = {
    BookingStatus.CANCELLED: {ActorRole.USER, ActorRole.ADMIN, ActorRole.SYSTEM},
    BookingStatus.VENDOR_ACCEPTED: {ActorRole.VENDOR, ActorRole.ADMIN},
    BookingStatus.VENDOR_COUNTERED: {ActorRole.VENDOR, ActorRole.ADMIN},
    BookingStatus.VENDOR_REJECTED: {ActorRole.VENDOR, ActorRole.ADMIN},
    BookingStatus.CONFIRMED: {ActorRole.SYSTEM, ActorRole.ADMIN, ActorRole.VENDOR},
    BookingStatus.IN_PROGRESS: {ActorRole.VENDOR, ActorRole.SYSTEM, ActorRole.ADMIN},
    BookingStatus.COMPLETED: {ActorRole.VENDOR, ActorRole.SYSTEM, ActorRole.ADMIN},
    BookingStatus.REFUND_PENDING: {ActorRole.SYSTEM, ActorRole.ADMIN},
    BookingStatus.REFUNDED: {ActorRole.SYSTEM, ActorRole.ADMIN},
    BookingStatus.EXPIRED: {ActorRole.SYSTEM, ActorRole.ADMIN},
    BookingStatus.PAYOUT_PENDING: {ActorRole.SYSTEM, ActorRole.ADMIN},
    BookingStatus.PAYOUT_RELEASED: {ActorRole.SYSTEM, ActorRole.ADMIN},
    BookingStatus.PAYMENT_PENDING_VERIFICATION: {ActorRole.SYSTEM, ActorRole.USER},
    BookingStatus.TOKEN_PAID: {ActorRole.SYSTEM, ActorRole.USER},
    BookingStatus.VENDOR_PENDING: {ActorRole.SYSTEM},
}


class BookingStateMachine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    def _allowed_targets(self, category: CategoryType, current_status: BookingStatus) -> Set[BookingStatus]:
        base_targets = BASE_TRANSITIONS.get(current_status, set()).copy()
        category_override = CATEGORY_OVERRIDES.get(category, {})
        if current_status in category_override:
            return category_override[current_status]
        return base_targets

    def assert_transition(
        self,
        *,
        category: CategoryType,
        current_status: BookingStatus,
        next_status: BookingStatus,
        actor: ActorRole,
    ) -> None:
        if next_status not in self._allowed_targets(category, current_status):
            raise HTTPException(
                status_code=409,
                detail=f"Transition not allowed: {current_status.value} -> {next_status.value}",
            )

        allowed_roles = ROLE_GUARDS.get(next_status, {ActorRole.SYSTEM, ActorRole.ADMIN})
        if actor not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role {actor.value} cannot transition booking to {next_status.value}",
            )

    async def transition_booking(
        self,
        *,
        booking_id: str,
        category: CategoryType,
        actor: ActorRole,
        expected_status: BookingStatus,
        expected_version: int,
        next_status: BookingStatus,
        reason: str | None,
        actor_id: str | None,
    ) -> Dict:
        self.assert_transition(
            category=category,
            current_status=expected_status,
            next_status=next_status,
            actor=actor,
        )

        now = datetime.now(timezone.utc)
        updated = await self.db.be_bookings.find_one_and_update(
            {
                "id": booking_id,
                "status": expected_status.value,
                "version": expected_version,
            },
            {
                "$set": {
                    "status": next_status.value,
                    "updated_at": now,
                },
                "$inc": {"version": 1},
            },
            return_document=ReturnDocument.AFTER,
            projection={"_id": 0},
        )

        if not updated:
            raise HTTPException(status_code=409, detail="Booking version/status conflict")

        await self.db.be_state_transitions.insert_one(
            {
                "booking_id": booking_id,
                "category_type": category.value,
                "from_status": expected_status.value,
                "to_status": next_status.value,
                "reason": reason,
                "actor": actor.value,
                "actor_id": actor_id,
                "created_at": now,
            }
        )

        return updated
