from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, Enum):
    CUSTOMER = "customer"
    VENDOR = "vendor"
    ADMIN = "admin"
    SYSTEM = "system"


class CategoryType(str, Enum):
    SERVICE = "service"
    GROCERY = "grocery"
    RENTAL = "rental"


class BookingIntentStatus(str, Enum):
    PENDING = "PENDING"
    EXPIRED = "EXPIRED"
    CONVERTED = "CONVERTED"


class BookingStatus(str, Enum):
    PENDING = "PENDING"
    AWAITING_PAYMENT = "AWAITING_PAYMENT"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    DISPUTED = "DISPUTED"
    REFUNDED = "REFUNDED"


class BookingAction(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    MARK_PROGRESS = "mark_progress"
    COMPLETE = "complete"
    CANCEL = "cancel"
    CONFIRM_COMPLETION = "confirm_completion"
    FORCE_REFUND = "force_refund"


class PaymentStatus(str, Enum):
    CREATED = "CREATED"
    CLIENT_VERIFIED = "CLIENT_VERIFIED"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class RefundStatus(str, Enum):
    REQUESTED = "REQUESTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class ResourceLockEntityType(str, Enum):
    SLOT = "SLOT"
    STOCK = "STOCK"


class ResourceLockStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


class StateEntityType(str, Enum):
    BOOKING = "BOOKING"
    PAYMENT = "PAYMENT"
    PAYOUT = "PAYOUT"


class LedgerEntryType(str, Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"
    HOLD = "HOLD"
    RELEASE = "RELEASE"


class PayoutStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    PROCESSED = "PROCESSED"
    REJECTED = "REJECTED"


class VendorStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    SUSPENDED = "SUSPENDED"
    REJECTED = "REJECTED"
    FEATURED = "FEATURED"


class QuoteStatus(str, Enum):
    PENDING = "PENDING"
    RESPONDED = "RESPONDED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class AmountType(BaseModel):
    """Canonical amount representation in integer paise."""

    model_config = ConfigDict(extra="forbid")
    value: int = Field(ge=0, description="Amount in paise")
    currency: str = Field(default="INR", min_length=3, max_length=3)


T = TypeVar("T")


class ResponseEnvelope(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")
    success: bool
    data: Optional[T] = None
    message: str = ""
    request_id: str = ""


class PaginationMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    page: int = Field(ge=1, default=1)
    page_size: int = Field(ge=1, le=200, default=20)
    total: int = Field(ge=0, default=0)


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")
    success: bool = True
    data: list[T] = []
    pagination: PaginationMeta = PaginationMeta()
    message: str = ""
    request_id: str = ""

