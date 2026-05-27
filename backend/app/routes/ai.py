from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ai_core.module import AIModule
from app.core.dependencies import get_ai_module_with_services, guard_ai_route
from app.core.security import get_current_user
from app.models.schemas import AIRollbackRequest

router = APIRouter(prefix="/ai", tags=["ai"], dependencies=[Depends(guard_ai_route)])


@router.get("/drift/status")
async def drift_status(
    _: dict = Depends(get_current_user),
    ai_module: AIModule = Depends(get_ai_module_with_services),
):
    return await ai_module.drift_monitor.status()


@router.get("/health")
async def ai_health(
    _: dict = Depends(get_current_user),
    ai_module: AIModule = Depends(get_ai_module_with_services),
):
    return await ai_module.profit_monitor.health()


@router.post("/rollback")
async def ai_rollback(
    payload: AIRollbackRequest,
    request: Request,
    user: dict = Depends(get_current_user),
    ai_module: AIModule = Depends(get_ai_module_with_services),
):
    ai_module.control_plane.require_admin(user)
    result = await ai_module.model_registry.rollback(payload)
    if result.get("status") != "ok":
        return result
    await ai_module.control_plane.rollback_log(
        model_type=payload.model_type,
        target_version=payload.target_version,
        actor=user.get("sub"),
    )
    return {"status": "ok", **result}
