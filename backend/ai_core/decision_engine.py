from __future__ import annotations

from app.models.schemas import DecisionRequest
from app.services.decision_service import DecisionService
from app.utils.websocket_manager import WebSocketManager


class DecisionEngine:
    def __init__(self, service: DecisionService) -> None:
        self.service = service

    async def score(self, payload: DecisionRequest):
        return await self.service.compute_book_now_score(payload)

    async def broadcast_score(self, ws_manager: WebSocketManager, payload: DecisionRequest, response) -> None:
        await ws_manager.broadcast(f"{payload.event_id}:{payload.vendor_id}", response.model_dump())

