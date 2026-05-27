from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from api.deps import get_db, get_razorpay_client
from auth import get_current_user
from booking_engine.schemas.payment import CreatePaymentOrderRequest, VerifyPaymentRequest
from booking_engine.services.payment_service import PaymentService
from booking_engine.services.jobs import schedule_sla_timeout_job

router = APIRouter(prefix="/api/booking-engine/payments", tags=["booking-engine-payments"])


def _payment_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
    razorpay_client=Depends(get_razorpay_client),
) -> PaymentService:
    return PaymentService(db, razorpay_client)


@router.post("/create-order")
async def create_order(
    req: CreatePaymentOrderRequest,
    payment_service: PaymentService = Depends(_payment_service),
    current_user: dict = Depends(get_current_user),
):
    return await payment_service.create_order(
        intent_id=req.intent_id,
        idempotency_key=req.idempotency_key,
        current_user=current_user,
    )


@router.post("/verify")
async def verify(
    req: VerifyPaymentRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    payment_service: PaymentService = Depends(_payment_service),
    current_user: dict = Depends(get_current_user),
):
    result = await payment_service.verify_payment(
        intent_id=req.intent_id,
        razorpay_order_id=req.razorpay_order_id,
        razorpay_payment_id=req.razorpay_payment_id,
        razorpay_signature=req.razorpay_signature,
        idempotency_key=req.idempotency_key,
        current_user=current_user,
    )

    booking = await db.be_bookings.find_one({"id": result["booking_id"]}, {"_id": 0, "status": 1})
    if booking and booking.get("status") == "vendor_pending":
        await schedule_sla_timeout_job(db, result["booking_id"], minutes=30)

    return result


@router.post("/webhook")
async def webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(default=None),
    payment_service: PaymentService = Depends(_payment_service),
):
    if not x_razorpay_signature:
        raise HTTPException(status_code=400, detail="Missing webhook signature")
    raw_body = await request.body()
    return await payment_service.process_webhook(raw_body=raw_body, signature=x_razorpay_signature)
