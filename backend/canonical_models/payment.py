from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from canonical_models.common import PaymentStatus, RefundStatus, utcnow


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class PaymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    booking_id: Optional[str] = None
    booking_intent_id: Optional[str] = None
    razorpay_order_id: str
    amount_paise: int = Field(ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    idempotency_key: str = Field(min_length=8, max_length=200)


class Payment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: _new_id("pay"))
    booking_id: Optional[str] = None
    booking_intent_id: Optional[str] = None
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    idempotency_key: str
    amount: int = Field(ge=0, description="Amount in paise")
    currency: str = Field(default="INR", min_length=3, max_length=3)
    status: PaymentStatus = PaymentStatus.CREATED
    webhook_received_at: Optional[datetime] = None
    meta: dict[str, Any] = {}
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class RefundCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    booking_id: str
    payment_id: str
    amount_paise: int = Field(ge=0)
    reason: str = Field(min_length=2, max_length=500)


class Refund(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: _new_id("ref"))
    booking_id: str
    payment_id: str
    razorpay_payment_id: Optional[str] = None
    razorpay_refund_id: Optional[str] = None
    amount_paise: int = Field(ge=0)
    reason: str
    status: RefundStatus = RefundStatus.REQUESTED
    requested_by: str = "system"
    meta: dict[str, Any] = {}
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

