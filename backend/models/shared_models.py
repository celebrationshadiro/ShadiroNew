"""Shared enums, base types, and common models used across multiple domains."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


# --- Shared Enums -----------------------------------------------------------
class EventType(str, Enum):
    WEDDING = "wedding"
    CORPORATE = "corporate"
    BIRTHDAY = "birthday"
    ANNIVERSARY = "anniversary"
    OTHER = "other"


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class BookingContext(str, Enum):
    GROCERY = "GROCERY"
    SERVICE = "SERVICE"


class AddressType(str, Enum):
    DELIVERY = "delivery"
    EVENT = "event"


class CopilotTone(str, Enum):
    FORMAL = "formal"
    QUICK = "quick"
    CONCISE = "concise"


class QuoteStatus(str, Enum):
    PENDING = "pending"
    RESPONDED = "responded"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class PackageTier(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    CUSTOM = "custom"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class PerformedBy(str, Enum):
    ADMIN = "admin"
    VENDOR = "vendor"
    SYSTEM = "system"


class AdminActionType(str, Enum):
    VENDOR_APPROVE = "vendor_approve"
    VENDOR_REJECT = "vendor_reject"
    VENDOR_SUSPEND = "vendor_suspend"
    VENDOR_FEATURED = "vendor_featured"
    VENDOR_REQUEST_CHANGES = "vendor_request_changes"
    USER_BLOCKED = "user_blocked"
    USER_ACTIVATED = "user_activated"
    PAYMENT_REFUND = "payment_refund"
    DISPUTE_RESOLVED = "dispute_resolved"
    OTHER = "other"


# --- Copilot request/response DTOs ---
class QuoteDraftRequest(BaseModel):
    quote_id: Optional[str] = None
    vendor_id: Optional[str] = None
    event_id: Optional[str] = None
    category_id: Optional[str] = None
    requested_services: List[str] = []
    message: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    tone: Optional[CopilotTone] = None


class QuoteDraftResponse(BaseModel):
    draft: str
    reasoning: str
    upsells: List[str] = []
    suggested_price: Optional[float] = None
    provider: str
    ai_enabled: bool = True
    confidence: float = 0.0
    metadata: Dict[str, Any] = {}


class NegotiationSummaryRequest(BaseModel):
    chat_id: Optional[str] = None
    messages: List[Dict[str, Any]] = []


class NegotiationSummaryResponse(BaseModel):
    summary: str
    key_points: List[str] = []
    next_steps: List[str] = []
    provider: str
    ai_enabled: bool = True
    confidence: float = 0.0
    metadata: Dict[str, Any] = {}


class ReplySuggestRequest(BaseModel):
    chat_id: Optional[str] = None
    messages: List[Dict[str, Any]] = []
    tone: Optional[CopilotTone] = None


class ReplySuggestResponse(BaseModel):
    suggestions: List[str] = []
    tone: Optional[str] = None
    provider: str
    ai_enabled: bool = True
    confidence: float = 0.0
    metadata: Dict[str, Any] = {}


# --- Shared Address models ---
class EventAddress(BaseModel):
    """Structured address for on-site services."""
    model_config = ConfigDict(extra="ignore")
    label: Optional[str] = None
    address_type: Optional[str] = AddressType.EVENT.value
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    landmark: Optional[str] = None
    venue_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    map_pin: Optional[Dict[str, float]] = None
    notes: Optional[str] = None


class GroceryDeliveryAddress(BaseModel):
    model_config = ConfigDict(extra="ignore")
    label: Optional[str] = None
    address_type: Optional[str] = AddressType.DELIVERY.value
    name: str
    phone: str
    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    landmark: Optional[str] = None
    instructions: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: bool = False
    zone: Optional[str] = None


# --- Pricing models (shared by vendor + admin) ---
class PricingRule(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    label: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    days_of_week: List[str] = []
    multiplier: Optional[float] = None
    flat_fee: Optional[float] = None


class PricingPreviewRequest(BaseModel):
    vendor_id: str
    event_date: Optional[str] = None
    base_amount: Optional[float] = None


class PricingPreviewResponse(BaseModel):
    vendor_id: str
    base_amount: float
    multiplier: float
    flat_fee: float
    total: float
    applied_rules: List[Dict[str, Any]] = []


# --- Admin / analytics shared ---
class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str
    performed_by: "PerformedBy"
    entity_type: str
    entity_id: str
    old_value: Dict[str, Any] = {}
    new_value: Dict[str, Any] = {}
    performed_by_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VendorApprovalAction(BaseModel):
    action: str
    reason: Optional[str] = None


class VendorCommissionUpdate(BaseModel):
    commission_percentage: Optional[float] = None
    minimum_commission: Optional[float] = None


class AdminAnalytics(BaseModel):
    total_users: int
    total_vendors: int
    pending_vendor_approvals: int
    total_revenue: float
    monthly_bookings: List[Dict[str, Any]] = []
    category_demand: List[Dict[str, Any]] = []


class AdminAuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    action_type: AdminActionType
    target_type: str
    target_id: str
    details: Dict[str, Any] = {}
    reason: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: Optional[str] = None
    success: bool = True


# --- Vendor media ---
class MediaAsset(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    alt_text: Optional[str] = None
    order: int = 0
