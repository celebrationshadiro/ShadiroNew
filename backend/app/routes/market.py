from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_market_signal_service, guard_ai_route
from app.core.security import get_current_user
from app.services.market_signal_service import MarketSignalService

router = APIRouter(prefix="/market", tags=["market"], dependencies=[Depends(guard_ai_route)])


@router.get("/price/forecast")
async def market_price_forecast(
    category: str = Query(..., min_length=1),
    city: str = Query(..., min_length=1),
    _: dict = Depends(get_current_user),
    market_signal_service: MarketSignalService = Depends(get_market_signal_service),
):
    return await market_signal_service.get_price_forecast(category=category, city=city)
