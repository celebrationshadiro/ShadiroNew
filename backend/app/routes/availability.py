from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_availability_service
from app.core.security import get_current_user
from app.models.schemas import AvailabilityRequest
from app.services.availability_service import AvailabilityService

router = APIRouter(prefix="/availability", tags=["availability"])


@router.post("/check")
async def check_availability(
    payload: AvailabilityRequest,
    _: dict = Depends(get_current_user),
    service: AvailabilityService = Depends(get_availability_service),
):
    return await service.check_realtime_availability(payload)

