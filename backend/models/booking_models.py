"""Booking domain models: bookings, orders, events, quotes, packages, reviews, services."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

from .shared_models import (
    BookingContext, EventType, OrderStatus, QuoteStatus, PackageTier,
    EventAddress, GroceryDeliveryAddress,
)


# --- Booking status ---
class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    VENDOR_ACCEPTED = "vendor_accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED_BY_USER = "cancelled_by_user"
    CANCELLED_BY_VENDOR = "cancelled_by_vendor"
    CANCELLED_BY_VENDOR_EMERGENCY = "cancelled_by_vendor_emergency"
    RESOLVED = "resolved"
    REFUNDED = "refunded"
    ESCALATED = "escalated"


# --- Events ---
class EventBase(BaseModel):
    event_type: EventType
    title: str
    date: str
    location: Optional[str] = None
    city: Optional[str] = None
    venue_type: Optional[str] = None
    map_pin: Optional[Dict[str, float]] = None
    guest_count: Optional[int] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    description: Optional[str] = None


class EventCreate(EventBase):
    pass


class Event(EventBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True


# --- Quotes ---
class QuoteBase(BaseModel):
    event_id: str
    vendor_id: str
    requested_services: List[str] = []
    message: Optional[str] = None


class QuoteCreate(QuoteBase):
    attachments: List[Dict[str, Any]] = []


class QuoteResponse(BaseModel):
    quote_id: str
    quoted_price: float
    response_message: Optional[str] = None
    services_offered: List[str] = []


class Quote(QuoteBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    status: QuoteStatus = QuoteStatus.PENDING
    quoted_price: Optional[float] = None
    response_message: Optional[str] = None
    services_offered: List[str] = []
    attachments: List[Dict[str, Any]] = []
    lead_score: Optional[int] = None
    lead_score_label: Optional[str] = None
    lead_score_reasons: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    responded_at: Optional[datetime] = None


# --- Packages ---
class PackageBase(BaseModel):
    vendor_id: str
    name: str
    description: Optional[str] = None
    tier: PackageTier = PackageTier.BASIC
    price: float = 0.0
    min_guests: Optional[int] = None
    max_guests: Optional[int] = None
    services_included: List[str] = []
    items_included: List[Dict[str, Any]] = []
    is_active: bool = True


class PackageCreate(PackageBase):
    pass


class Package(PackageBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Orders ---
class OrderBase(BaseModel):
    user_id: str
    vendor_id: Optional[str] = None
    event_id: str
    package_id: Optional[str] = None
    quote_id: Optional[str] = None
    total_amount: float
    commission_percentage: Optional[float] = None
    minimum_commission: Optional[float] = None
    commission_amount: Optional[float] = None
    vendor_payout_amount: Optional[float] = None
    gateway_fee: Optional[float] = None
    services: List[str] = []
    selected_items: List[Dict[str, Any]] = []
    pricing_mode: Optional[str] = None  # "package" | "custom" | "base"
    booking_context: Optional[BookingContext] = BookingContext.SERVICE
    event_location: Optional[str] = None
    event_city: Optional[str] = None
    event_date: Optional[str] = None
    venue_type: Optional[str] = None
    event_location_lat: Optional[float] = None
    event_location_lng: Optional[float] = None
    event_location_notes: Optional[str] = None
    ai_context_address: Optional[Dict[str, Any]] = None


class OrderCreate(OrderBase):
    pass


class Order(OrderBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: OrderStatus = OrderStatus.PENDING
    payment_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Booking items ---
class BookingItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    qty: int = 1
    unit_price: float = 0.0
    total_price: float = 0.0
    notes: Optional[str] = None


class AddOn(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    qty: int = 1
    price: float = 0.0


class Booking(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    vendor_id: Optional[str] = None
    event_id: Optional[str] = None
    package_id: Optional[str] = None
    items: List[BookingItem] = []
    add_ons: List[AddOn] = []
    booking_context: Optional[BookingContext] = BookingContext.SERVICE
    event_address: Optional[EventAddress] = None
    delivery_address: Optional[GroceryDeliveryAddress] = None
    event_city: Optional[str] = None
    venue_type: Optional[str] = None
    event_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    event_location_notes: Optional[str] = None
    ai_context_address: Optional[Dict[str, Any]] = None
    category_id: Optional[str] = None
    category_flow_version: Optional[str] = None
    category_booking_details: Dict[str, Any] = {}
    pricing_snapshot: Dict[str, Any] = {}
    payment_plan: Dict[str, Any] = {}
    special_instructions: Optional[str] = None
    total_amount: float = 0.0
    advance_paid: float = 0.0
    payment_id: Optional[str] = None
    status: BookingStatus = BookingStatus.PENDING
    emergency_reason: Optional[str] = None
    emergency_notified_admin: bool = False
    replacement_vendor_id: Optional[str] = None
    replacement_suggestions: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


# --- Reviews ---
class ReviewBase(BaseModel):
    vendor_id: str
    order_id: Optional[str] = None
    rating: int
    comment: Optional[str] = None


class ReviewCreate(ReviewBase):
    pass


class Review(ReviewBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Service definitions ---
class ServiceItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    category_id: str
    name: str
    description: Optional[str] = None
    unit_price: float
    unit: str = "item"
    service_category: Optional[str] = None
    is_available: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ServiceDefinition(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    category_id: str
    service_items: List[ServiceItem] = []
    availability_start_date: Optional[str] = None
    availability_end_date: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
