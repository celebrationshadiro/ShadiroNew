from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Request, status
from pydantic import BaseModel, ConfigDict, Field

from canonical_models.common import ResponseEnvelope

router = APIRouter(prefix="/api/grocery/payments", tags=["grocery_payments"])
logger = logging.getLogger(__name__)


class MockPaymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_id: str = Field(min_length=8)
    amount_paise: int = Field(gt=0)


@router.post("/mock-paid/{user_id}", response_model=ResponseEnvelope[dict])
async def mock_payment_paid(
    user_id: str,
    payload: MockPaymentRequest,
    request: Request,
) -> ResponseEnvelope[dict]:
    """
    Simulate a successful payment for a grocery order.
    Emits the ORDER_PAID event to both the 'ws:notifications' and 'ws:delivery' channels.
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
        "event": "ORDER_PAID",
        "order_id": payload.order_id,
        "amount_paise": payload.amount_paise,
        "status": "success",
        "message": f"Your payment of {payload.amount_paise / 100:.2f} INR for order {payload.order_id} was successfully processed.",
    }

    # Emit to notifications channel
    await broker.publish(user_id, event_payload, channel_prefix="ws:notifications")
    
    # Emit to delivery channel
    await broker.publish(user_id, event_payload, channel_prefix="ws:delivery")

    logger.info(f"Mock ORDER_PAID websocket events dispatched to user_id={user_id} for order_id={payload.order_id}")

    return ResponseEnvelope[dict](
        success=True,
        data={"user_id": user_id, "order_id": payload.order_id, "status": "ORDER_PAID"},
        message="Payment success event dispatched",
        request_id=getattr(request.state, "request_id", ""),
    )


@router.post("/mock-failed/{user_id}", response_model=ResponseEnvelope[dict])
async def mock_payment_failed(
    user_id: str,
    payload: MockPaymentRequest,
    request: Request,
) -> ResponseEnvelope[dict]:
    """
    Simulate a failed payment for a grocery order.
    Emits a PAYMENT_FAILED event to the 'ws:notifications' channel.
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
        "event": "PAYMENT_FAILED",
        "order_id": payload.order_id,
        "amount_paise": payload.amount_paise,
        "status": "failed",
        "message": f"Your payment of {payload.amount_paise / 100:.2f} INR for order {payload.order_id} failed. Please try again.",
    }

    # Emit to notifications channel
    await broker.publish(user_id, event_payload, channel_prefix="ws:notifications")

    logger.info(f"Mock PAYMENT_FAILED websocket event dispatched to user_id={user_id} for order_id={payload.order_id}")

    return ResponseEnvelope[dict](
        success=True,
        data={"user_id": user_id, "order_id": payload.order_id, "status": "PAYMENT_FAILED"},
        message="Payment failure event dispatched",
        request_id=getattr(request.state, "request_id", ""),
    )
