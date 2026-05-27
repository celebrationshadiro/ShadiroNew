from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PaginatedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[dict[str, Any]]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    has_next: bool = False


class CategoryUpsert(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    icon: Optional[str] = Field(default=None, max_length=100)
    image_url: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = True
    sort_order: int = 100


class VendorCreate(BaseModel):
    model_config = ConfigDict(extra="allow")
    business_name: str = Field(min_length=2, max_length=200)
    category_id: str = Field(min_length=2, max_length=100)
    vendor_type: str = "service_vendor"
    description: Optional[str] = Field(default=None, max_length=5000)
    location: Optional[str] = Field(default=None, max_length=300)
    city: Optional[str] = Field(default=None, max_length=120)
    base_price: Optional[float] = Field(default=None, ge=0)
    service_areas: list[str] = Field(default_factory=list)
    pricing_rules: list[dict[str, Any]] = Field(default_factory=list)
    media: list[dict[str, Any]] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class VendorPatch(BaseModel):
    model_config = ConfigDict(extra="allow")
    business_name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    category_id: Optional[str] = Field(default=None, min_length=2, max_length=100)
    vendor_type: Optional[str] = None
    description: Optional[str] = Field(default=None, max_length=5000)
    location: Optional[str] = Field(default=None, max_length=300)
    city: Optional[str] = Field(default=None, max_length=120)
    base_price: Optional[float] = Field(default=None, ge=0)
    service_areas: Optional[list[str]] = None
    pricing_rules: Optional[list[dict[str, Any]]] = None
    media: Optional[list[dict[str, Any]]] = None
    details: Optional[dict[str, Any]] = None
    is_available: Optional[bool] = None
    availability_note: Optional[str] = None
    next_available_date: Optional[str] = None


class PackageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vendor_id: str
    name: str = Field(min_length=2, max_length=200)
    description: Optional[str] = Field(default=None, max_length=3000)
    tier: str = "basic"
    price: float = Field(default=0, ge=0)
    min_guests: Optional[int] = Field(default=None, ge=1)
    max_guests: Optional[int] = Field(default=None, ge=1)
    services_included: list[str] = Field(default_factory=list)
    items_included: list[dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True


class PackagePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    description: Optional[str] = Field(default=None, max_length=3000)
    tier: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0)
    min_guests: Optional[int] = Field(default=None, ge=1)
    max_guests: Optional[int] = Field(default=None, ge=1)
    services_included: Optional[list[str]] = None
    items_included: Optional[list[dict[str, Any]]] = None
    is_active: Optional[bool] = None


class EventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_type: str
    title: str = Field(min_length=2, max_length=200)
    date: str
    location: Optional[str] = None
    city: Optional[str] = None
    venue_type: Optional[str] = None
    map_pin: Optional[dict[str, float]] = None
    guest_count: Optional[int] = Field(default=None, ge=1)
    budget_min: Optional[float] = Field(default=None, ge=0)
    budget_max: Optional[float] = Field(default=None, ge=0)
    description: Optional[str] = Field(default=None, max_length=5000)


class QuoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str
    vendor_id: str
    requested_services: list[str] = Field(default_factory=list)
    message: Optional[str] = Field(default=None, max_length=5000)
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class QuoteRespond(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quoted_price: float = Field(ge=0)
    response_message: Optional[str] = Field(default=None, max_length=5000)
    services_offered: list[str] = Field(default_factory=list)


class ReviewCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vendor_id: str
    order_id: Optional[str] = None
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=3000)


class PublicUserContact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    email: EmailStr


class TimestampedDocument(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
