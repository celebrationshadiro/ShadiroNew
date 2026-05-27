from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_pricing_service
from app.core.security import get_current_user
from app.models.schemas import PricingRequest
from app.services.pricing_service import PricingService

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/fairness")
async def price_fairness(
    payload: PricingRequest,
    _: dict = Depends(get_current_user),
    service: PricingService = Depends(get_pricing_service),
):
    return await service.compute_price_fairness(payload)

