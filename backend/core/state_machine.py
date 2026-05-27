from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from canonical_models.common import BookingStatus, StateEntityType, UserRole


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


DEFAULT_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
    BookingStatus.PENDING: {BookingStatus.AWAITING_PAYMENT, BookingStatus.CANCELLED},
    BookingStatus.AWAITING_PAYMENT: {BookingStatus.PAYMENT_RECEIVED, BookingStatus.CANCELLED},
    BookingStatus.PAYMENT_RECEIVED: {BookingStatus.CONFIRMED, BookingStatus.CANCELLED, BookingStatus.REFUNDED},
    BookingStatus.CONFIRMED: {BookingStatus.IN_PROGRESS, BookingStatus.CANCELLED, BookingStatus.DISPUTED},
    BookingStatus.IN_PROGRESS: {BookingStatus.COMPLETED, BookingStatus.CANCELLED, BookingStatus.DISPUTED},
    BookingStatus.COMPLETED: {BookingStatus.REFUNDED, BookingStatus.DISPUTED},
    BookingStatus.CANCELLED: {BookingStatus.REFUNDED, BookingStatus.DISPUTED},
    BookingStatus.DISPUTED: {BookingStatus.REFUNDED, BookingStatus.COMPLETED, BookingStatus.CANCELLED},
    BookingStatus.REFUNDED: set(),
}


ROLE_ALLOWED_TARGETS: dict[UserRole, set[BookingStatus]] = {
    UserRole.CUSTOMER: {BookingStatus.CANCELLED},
    UserRole.VENDOR: {BookingStatus.CONFIRMED, BookingStatus.COMPLETED, BookingStatus.CANCELLED},
    UserRole.ADMIN: set(BookingStatus),
    UserRole.SYSTEM: {BookingStatus.AWAITING_PAYMENT, BookingStatus.PAYMENT_RECEIVED, BookingStatus.REFUNDED},
}


class BookingStateMachine:
    """Canonical booking state machine with optimistic concurrency controls."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    @staticmethod
    def _normalize_role(role: UserRole | str) -> UserRole:
        value = role.value if isinstance(role, UserRole) else str(role).lower()
        try:
            return UserRole(value)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid actor role") from exc

    @staticmethod
    def _normalize_status(status_value: BookingStatus | str) -> BookingStatus:
        if isinstance(status_value, BookingStatus):
            return status_value
        try:
            return BookingStatus(str(status_value))
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid booking status") from exc

    def _allowed_targets(self, current: BookingStatus) -> set[BookingStatus]:
        return DEFAULT_TRANSITIONS.get(current, set())

    def _assert_role_target_allowed(
        self,
        *,
        actor_role: UserRole,
        current_status: BookingStatus,
        to_status: BookingStatus,
    ) -> None:
        role_targets = ROLE_ALLOWED_TARGETS.get(actor_role, set())
        if to_status not in role_targets:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {actor_role.value} cannot set status to {to_status.value}",
            )

        # customer can cancel only before confirmed
        if actor_role == UserRole.CUSTOMER and to_status == BookingStatus.CANCELLED:
            allowed_customer_cancel_from: Iterable[BookingStatus] = (
                BookingStatus.PENDING,
                BookingStatus.AWAITING_PAYMENT,
                BookingStatus.PAYMENT_RECEIVED,
            )
            if current_status not in allowed_customer_cancel_from:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Customer cancellation is only allowed before confirmed",
                )

    def assert_transition_allowed(
        self,
        *,
        from_status: BookingStatus | str,
        to_status: BookingStatus | str,
        actor_role: UserRole | str,
    ) -> None:
        current = self._normalize_status(from_status)
        target = self._normalize_status(to_status)
        role = self._normalize_role(actor_role)

        allowed_targets = self._allowed_targets(current)
        if target not in allowed_targets:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Invalid transition: {current.value} -> {target.value}",
            )

        if role != UserRole.ADMIN:
            self._assert_role_target_allowed(
                actor_role=role,
                current_status=current,
                to_status=target,
            )

    async def log_transition(
        self,
        *,
        booking_id: str,
        from_status: BookingStatus,
        to_status: BookingStatus,
        actor_role: UserRole,
        actor_id: str,
        reason: str | None = None,
    ) -> None:
        await self.db.state_transitions.insert_one(
            {
                "entity_type": StateEntityType.BOOKING.value,
                "entity_id": booking_id,
                "from_status": from_status.value,
                "to_status": to_status.value,
                "actor_role": actor_role.value,
                "actor_id": actor_id,
                "reason": reason,
                "created_at": utcnow(),
            }
        )

    async def transition_booking(
        self,
        *,
        booking_id: str,
        from_status: BookingStatus | str,
        to_status: BookingStatus | str,
        actor_role: UserRole | str,
        actor_id: str,
        current_version: int,
        reason: str | None = None,
    ) -> dict:
        current = self._normalize_status(from_status)
        target = self._normalize_status(to_status)
        role = self._normalize_role(actor_role)

        self.assert_transition_allowed(
            from_status=current,
            to_status=target,
            actor_role=role,
        )

        update_payload = {
            "status": target.value,
            "version": int(current_version) + 1,
            "updated_at": utcnow(),
        }
        if target == BookingStatus.COMPLETED:
            update_payload["completed_at"] = utcnow()
        if target in {BookingStatus.CANCELLED, BookingStatus.REFUNDED}:
            update_payload["cancelled_at"] = utcnow()

        result = await self.db.bookings.find_one_and_update(
            {
                "id": booking_id,
                "status": current.value,
                "version": int(current_version),
            },
            {"$set": update_payload},
            return_document=ReturnDocument.AFTER,
            projection={"_id": 0},
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conflict: stale state or invalid transition",
            )

        await self.log_transition(
            booking_id=booking_id,
            from_status=current,
            to_status=target,
            actor_role=role,
            actor_id=actor_id,
            reason=reason,
        )
        return result
