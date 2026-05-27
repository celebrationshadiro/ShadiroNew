from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_negotiation_service
from app.core.security import get_current_user
from app.models.schemas import NegotiationRequest
from app.services.negotiation_service import NegotiationService

router = APIRouter(prefix="/negotiation", tags=["negotiation"])


@router.post("/counter")
async def counter_offer(
    payload: NegotiationRequest,
    _: dict = Depends(get_current_user),
    service: NegotiationService = Depends(get_negotiation_service),
):
    return await service.negotiate(payload)

