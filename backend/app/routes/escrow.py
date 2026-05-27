from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_escrow_service
from app.core.security import get_current_user
from app.models.schemas import EscrowBookingRequest, ReleaseMilestoneRequest
from app.services.escrow_service import EscrowService

router = APIRouter(prefix="/escrow", tags=["escrow"])


@router.post("/bookings")
async def create_booking_with_escrow(
    payload: EscrowBookingRequest,
    _: dict = Depends(get_current_user),
    service: EscrowService = Depends(get_escrow_service),
):
    return await service.create_booking_with_escrow(payload)


@router.post("/milestones/release")
async def release_milestone(
    payload: ReleaseMilestoneRequest,
    _: dict = Depends(get_current_user),
    service: EscrowService = Depends(get_escrow_service),
):
    return await service.release_milestone(payload)


@router.post("/disputes/auto-trigger")
async def auto_trigger_disputes(
    _: dict = Depends(get_current_user),
    service: EscrowService = Depends(get_escrow_service),
):
    return await service.trigger_auto_disputes()

