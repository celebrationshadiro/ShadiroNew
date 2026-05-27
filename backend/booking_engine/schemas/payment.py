from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CreatePaymentOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent_id: str
    idempotency_key: str = Field(min_length=8, max_length=128)


class VerifyPaymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    idempotency_key: str = Field(min_length=8, max_length=128)


class PaymentOrderResponse(BaseModel):
    order_id: str
    amount: int
    currency: str
    key_id: str
    intent_id: str


class PaymentVerifyResponse(BaseModel):
    verified: bool
    booking_id: str
    booking_status: str
