"""Payment domain models: payments, ledger entries, payouts."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ConfigDict

from .shared_models import PaymentStatus


class LedgerStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REFUNDED = "refunded"
    ADJUSTED = "adjusted"


class PayoutStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    REJECTED = "rejected"


# --- Payment ---
class PaymentBase(BaseModel):
    order_id: str
    user_id: str
    amount: float
    payment_method: str = "razorpay"


class PaymentCreate(PaymentBase):
    razorpay_order_id: Optional[str] = None


class Payment(PaymentBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: PaymentStatus = PaymentStatus.PENDING
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Vendor ledger ---
class VendorLedgerEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    order_id: Optional[str] = None
    payout_id: Optional[str] = None
    source_type: str  # "service_order" | "grocery_order"
    gross_amount: float
    commission_percentage: float
    minimum_commission: float
    commission_amount: float
    net_amount: float
    gateway_fee: float = 0.0
    currency: str = "INR"
    status: LedgerStatus = LedgerStatus.CONFIRMED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Vendor payouts ---
class VendorPayoutRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    amount: float
    status: PayoutStatus = PayoutStatus.PENDING
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payout_date: Optional[datetime] = None
    admin_id: Optional[str] = None
    admin_note: Optional[str] = None
