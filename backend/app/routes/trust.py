from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_trust_service
from app.core.security import get_current_user
from app.models.schemas import TrustScoreRequest
from app.services.trust_service import TrustService

router = APIRouter(prefix="/trust", tags=["trust"])


@router.post("/score")
async def trust_score(
    payload: TrustScoreRequest,
    _: dict = Depends(get_current_user),
    service: TrustService = Depends(get_trust_service),
):
    return await service.compute_trust_score(payload)

