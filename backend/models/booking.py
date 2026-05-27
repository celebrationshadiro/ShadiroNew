from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from models.common import (
    BookingAction,
    BookingIntentStatus,
    BookingStatus,
    CategoryType,
    ResourceLockEntityType,
    ResourceLockStatus,
    StateEntityType,
    UserRole,
    utcnow,
)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class BookingLineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_id: str
    title: str
    qty: int = Field(ge=1)
    unit_price_paise: int = Field(ge=0)
    total_price_paise: int = Field(ge=0)
    meta: dict[str, Any] = {}

    @model_validator(mode="after")
    def validate_total(self):
        expected = self.qty * self.unit_price_paise
        if self.total_price_paise != expected:
            raise ValueError("total_price_paise must be qty * unit_price_paise")
        return self


class BookingIntentBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idempotency_key: str = Field(min_length=8, max_length=128)
    vendor_id: str
    category_type: CategoryType
    items: list[BookingLineItem]
    total_amount_paise: int = Field(ge=0)
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=None, ge=0)
    notes: Optional[str] = None
    meta: dict[str, Any] = {}

    @model_validator(mode="after")
    def validate_total(self):
        expected = sum(item.total_price_paise for item in self.items)
        if self.total_amount_paise != expected:
            raise ValueError("total_amount_paise must match sum(items.total_price_paise)")
        return self


class BookingIntentCreate(BookingIntentBase):
    pass


class BookingIntent(BookingIntentBase):
    user_id: str
    id: str = Field(default_factory=lambda: _new_id("bint"))
    status: BookingIntentStatus = BookingIntentStatus.PENDING
    expires_at: datetime = Field(default_factory=lambda: utcnow() + timedelta(minutes=30))
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    version: int = Field(default=1, ge=1)


class BookingBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent_id: str
    user_id: str
    vendor_id: str
    category_type: CategoryType
    items: list[BookingLineItem]
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=None, ge=0)
    amount_gross_paise: int = Field(ge=0)
    commission_rate_bps: int = Field(ge=0, le=10000, description="Commission in basis points")
    commission_amount_paise: int = Field(ge=0)
    vendor_net_paise: int = Field(ge=0)
    payment_id: Optional[str] = None
    resource_lock_ids: list[str] = []
    notes: Optional[str] = None
    meta: dict[str, Any] = {}

    @model_validator(mode="after")
    def validate_financials(self):
        if self.commission_amount_paise > self.amount_gross_paise:
            raise ValueError("commission_amount_paise cannot exceed amount_gross_paise")
        if self.vendor_net_paise != self.amount_gross_paise - self.commission_amount_paise:
            raise ValueError("vendor_net_paise must equal gross - commission")
        return self


class BookingCreate(BookingBase):
    pass


class Booking(BookingBase):
    id: str = Field(default_factory=lambda: _new_id("book"))
    status: BookingStatus = BookingStatus.PENDING
    version: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None


class ResourceLockBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entity_type: ResourceLockEntityType
    entity_id: str
    booking_intent_id: str
    locked_qty: int = Field(ge=1)
    status: ResourceLockStatus = ResourceLockStatus.ACTIVE


class ResourceLockCreate(ResourceLockBase):
    ttl_minutes: int = Field(default=15, ge=1, le=120)


class ResourceLock(ResourceLockBase):
    id: str = Field(default_factory=lambda: _new_id("lock"))
    expires_at: datetime = Field(default_factory=lambda: utcnow() + timedelta(minutes=15))
    released_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)

    @field_validator("expires_at")
    @classmethod
    def ensure_future_expiry(cls, value: datetime) -> datetime:
        if value <= utcnow():
            raise ValueError("expires_at must be in the future")
        return value


class StateTransitionBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entity_type: StateEntityType = StateEntityType.BOOKING
    entity_id: str
    from_status: str
    to_status: str
    actor_role: UserRole
    actor_id: str
    reason: Optional[str] = None
    meta: dict[str, Any] = {}


class StateTransition(StateTransitionBase):
    id: str = Field(default_factory=lambda: _new_id("st"))
    created_at: datetime = Field(default_factory=utcnow)


class BookingTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["transition"] = "transition"
    to_status: BookingStatus
    expected_from_status: BookingStatus
    expected_version: int = Field(ge=1)
    reason: Optional[str] = None


class BookingActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: BookingAction
    expected_version: int = Field(ge=1)
    reason: Optional[str] = None
