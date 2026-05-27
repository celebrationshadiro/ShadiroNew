from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Request, status
from pydantic import BaseModel, ConfigDict, Field

from canonical_models.common import ResponseEnvelope

router = APIRouter(prefix="/api/grocery/vendor", tags=["grocery_vendor"])
logger = logging.getLogger(__name__)


class MockStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    suborder_id: str = Field(min_length=8)
    status: str = Field(pattern="^(PROCESSING|SHIPPED|DELIVERED)$")


@router.post("/mock-status-update/{user_id}", response_model=ResponseEnvelope[dict])
async def mock_suborder_status_update(
    user_id: str,
    payload: MockStatusUpdateRequest,
    request: Request,
) -> ResponseEnvelope[dict]:
    """
    Simulate a suborder status update by a vendor.
    Emits the SUBORDER_STATUS_UPDATE event to both the 'ws:delivery' and 'ws:notifications' channels.
    """
    broker = getattr(request.app.state, "websocket_broker", None)
    if not broker:
        logger.error("WebSocket broker not initialized on app.state")
        return ResponseEnvelope[dict](
            success=False,
            data={},
            message="WebSocket broker unavailable",
            request_id=getattr(request.state, "request_id", ""),
        )

    event_payload = {
        "event": "SUBORDER_STATUS_UPDATE",
        "suborder_id": payload.suborder_id,
        "status": payload.status,
        "message": f"Your suborder {payload.suborder_id} has been marked as {payload.status}.",
    }

    # Emit to delivery channel
    await broker.publish(user_id, event_payload, channel_prefix="ws:delivery")
    
    # Emit to notifications channel
    await broker.publish(user_id, event_payload, channel_prefix="ws:notifications")

    logger.info(f"Mock SUBORDER_STATUS_UPDATE websocket events dispatched to user_id={user_id} for suborder_id={payload.suborder_id} with status={payload.status}")

    return ResponseEnvelope[dict](
        success=True,
        data={"user_id": user_id, "suborder_id": payload.suborder_id, "status": payload.status},
        message="Suborder status update event dispatched",
        request_id=getattr(request.state, "request_id", ""),
    )
