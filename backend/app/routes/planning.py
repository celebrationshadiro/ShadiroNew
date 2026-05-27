from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_planning_service
from app.core.security import get_current_user
from app.models.schemas import PlanningRequest
from app.services.planning_service import PlanningService

router = APIRouter(prefix="/planning", tags=["planning"])


@router.post("/plan")
async def create_plan(
    payload: PlanningRequest,
    _: dict = Depends(get_current_user),
    service: PlanningService = Depends(get_planning_service),
):
    return await service.create_or_update_plan(payload)

