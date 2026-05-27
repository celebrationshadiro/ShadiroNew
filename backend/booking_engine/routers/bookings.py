from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from api.deps import get_db
from auth import get_current_user
from booking_engine.core.booking_orchestrator import BookingOrchestrator
from booking_engine.core.state_machine import BookingStateMachine
from booking_engine.models.booking_models import ActorRole, BookingStatus, CategoryType
from booking_engine.schemas.booking import BookingTransitionRequest

router = APIRouter(prefix="/api/booking-engine/bookings", tags=["booking-engine-bookings"])


def _actor_from_user(user: dict) -> ActorRole:
    role = str(user.get("role", "")).lower()
    if role == "admin":
        return ActorRole.ADMIN
    if role == "vendor":
        return ActorRole.VENDOR
    return ActorRole.USER


@router.post("")
async def create_booking(
    payload: dict,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    orchestrator = BookingOrchestrator(db)
    return await orchestrator.create_booking_intent(payload, current_user)


@router.get("/{booking_id}")
async def get_booking(
    booking_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    booking = await db.be_bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    role = _actor_from_user(current_user)
    if role == ActorRole.USER and booking["user_id"] != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    if role == ActorRole.VENDOR:
        vendor = await db.vendors.find_one({"user_id": current_user["sub"]}, {"_id": 0, "id": 1})
        if not vendor or vendor["id"] != booking["vendor_id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

    return booking


@router.post("/{booking_id}/transition")
async def transition_booking(
    booking_id: str,
    req: BookingTransitionRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    booking = await db.be_bookings.find_one({"id": booking_id}, {"_id": 0, "category_type": 1, "vendor_id": 1, "user_id": 1})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    actor = _actor_from_user(current_user)
    if actor == ActorRole.USER and booking["user_id"] != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    if actor == ActorRole.VENDOR:
        vendor = await db.vendors.find_one({"user_id": current_user["sub"]}, {"_id": 0, "id": 1})
        if not vendor or vendor["id"] != booking["vendor_id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

    state_machine = BookingStateMachine(db)
    updated = await state_machine.transition_booking(
        booking_id=booking_id,
        category=CategoryType(booking["category_type"]),
        actor=actor,
        expected_status=BookingStatus(req.expected_status.value),
        expected_version=req.expected_version,
        next_status=BookingStatus(req.to_status.value),
        reason=req.reason,
        actor_id=current_user.get("sub"),
    )
    return updated
