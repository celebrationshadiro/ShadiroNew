from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, status

from ai_core.module import AIModule
from app.core.dependencies import get_ai_module_with_services, guard_ai_route
from app.core.security import decode_token, get_current_user
from app.models.schemas import DecisionRequest
from app.utils.websocket_manager import WebSocketManager

router = APIRouter(prefix="/decision", tags=["decision"], dependencies=[Depends(guard_ai_route)])


@router.post("/book-now-score")
async def book_now_score(
    payload: DecisionRequest,
    request: Request,
    ai_module: AIModule = Depends(get_ai_module_with_services),
):
    if not payload.request_id:
        payload.request_id = getattr(request.state, "correlation_id", None)
    result = await ai_module.decision_engine.score(payload)
    ws_manager: WebSocketManager = request.app.state.ws_manager
    await ai_module.decision_engine.broadcast_score(ws_manager, payload, result)
    return result


@router.get("/model/performance")
async def model_performance(
    _: dict = Depends(get_current_user),
    ai_module: AIModule = Depends(get_ai_module_with_services),
):
    return await ai_module.model_registry.get_decision_performance()


@router.post("/model/calibrate")
async def calibrate_model(
    user: dict = Depends(get_current_user),
    ai_module: AIModule = Depends(get_ai_module_with_services),
):
    ai_module.control_plane.require_admin(user)
    return await ai_module.model_registry.calibrate_decision_model(actor=user.get("sub", "unknown"))


def mount_decision_ws(router: APIRouter, ws_manager: WebSocketManager, settings) -> None:
    @router.websocket("/ws/{event_id}/{vendor_id}")
    async def decision_ws(websocket: WebSocket, event_id: str, vendor_id: str) -> None:
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        try:
            decode_token(token, settings)
        except HTTPException:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        channel = f"{event_id}:{vendor_id}"
        await ws_manager.connect(channel, websocket)
        try:
            while True:
                _ = await websocket.receive_text()
        except WebSocketDisconnect:
            await ws_manager.disconnect(channel, websocket)
