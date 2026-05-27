from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from booking_engine.models.booking_models import BookingStatus, CategoryType


class BaseBookingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vendor_id: str
    category_type: CategoryType
    event_id: Optional[str] = None
    notes: Optional[str] = None
    idempotency_key: str = Field(min_length=8, max_length=128)


class ServiceBookingCreate(BaseBookingCreate):
    category_type: CategoryType = CategoryType.SERVICE
    event_date: str
    start_time: str
    end_time: str
    event_city: str
    event_location: str
    items: List[Dict[str, Any]] = []
    token_amount: float = Field(gt=0)


class GroceryItemInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_id: str
    qty: int = Field(gt=0)


class GroceryBookingCreate(BaseBookingCreate):
    category_type: CategoryType = CategoryType.GROCERY
    delivery_address: Dict[str, Any]
    items: List[GroceryItemInput]
    payment_amount: float = Field(gt=0)


class RentalBookingCreate(BaseBookingCreate):
    category_type: CategoryType = CategoryType.RENTAL
    rental_start: datetime
    rental_end: datetime
    inventory_item_id: str
    qty: int = Field(gt=0)
    rental_amount: float = Field(gt=0)
    deposit_amount: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_rental_window(self):
        if self.rental_end <= self.rental_start:
            raise ValueError("rental_end must be greater than rental_start")
        return self


class BookingIntentResponse(BaseModel):
    intent_id: str
    booking_id: Optional[str] = None
    state: str
    category_type: CategoryType
    requires_payment: bool
    payment_payload: Optional[Dict[str, Any]] = None


class BookingTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    to_status: BookingStatus
    expected_status: BookingStatus
    expected_version: int = Field(ge=1)
    reason: Optional[str] = None


class BookingView(BaseModel):
    id: str
    intent_id: str
    category_type: CategoryType
    status: BookingStatus
    version: int
    user_id: str
    vendor_id: str
    payload: Dict[str, Any]
    payment_summary: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


def resolve_create_schema(payload: Dict[str, Any]):
    category = str(payload.get("category_type", "")).lower()
    if category == CategoryType.SERVICE.value:
        return ServiceBookingCreate.model_validate(payload)
    if category == CategoryType.GROCERY.value:
        return GroceryBookingCreate.model_validate(payload)
    if category == CategoryType.RENTAL.value:
        return RentalBookingCreate.model_validate(payload)
    raise ValueError("Unsupported category_type")
