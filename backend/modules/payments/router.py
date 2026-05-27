from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Form, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, ConfigDict, Field

from api.deps import get_db, get_razorpay_client
from auth import get_current_user
from core.config import get_settings

from .repository import PaymentRepository
from .service import PaymentService

router = APIRouter(prefix="/api/payments", tags=["payments"])
logger = logging.getLogger(__name__)


class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_id: str = Field(min_length=1)


def get_payment_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
    razorpay_client=Depends(get_razorpay_client),
) -> PaymentService:
    settings = get_settings()
    repo = PaymentRepository(db)
    return PaymentService(repo, razorpay_client, settings.RAZORPAY_KEY_ID)


@router.post(
    "/create-order",
    description="Deprecated query-param form removed. Send `order_id` in JSON body. Prefer /api/bookings/{intent_id}/pay.",
)
async def create_razorpay_order(
    payload: CreateOrderRequest,
    current_user: dict = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
):
    return await payment_service.create_order(payload.order_id, current_user)


@router.post("/verify")
async def verify_payment(
    razorpay_order_id: str = Form(...),
    razorpay_payment_id: str = Form(...),
    razorpay_signature: str = Form(...),
    order_id: str = Form(...),
    current_user: dict = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
):
    try:
        return await payment_service.verify_order_payment(
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
            order_id=order_id,
            current_user=current_user,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment verification failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Payment verification failed")
