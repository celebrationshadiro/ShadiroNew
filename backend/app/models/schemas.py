from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class EventPreferences(BaseModel):
    budget: float = Field(gt=0)
    style: Optional[str] = None
    attendee_count: int = Field(gt=0, le=100000)
    location_city: str
    categories: List[str] = Field(min_length=1, max_length=10)


class PlanningRequest(BaseModel):
    event_id: str
    user_id: str
    event_date: datetime
    preferences: EventPreferences


class AvailabilityRequest(BaseModel):
    event_id: str
    category: str
    city: str
    start_at: datetime
    end_at: datetime
    vendor_ids: List[str] = Field(default_factory=list)


class PricingRequest(BaseModel):
    event_id: str
    vendor_id: str
    category: str
    quoted_price: float = Field(gt=0)
    attendee_count: int = Field(gt=0)
    city: str


class TrustScoreRequest(BaseModel):
    vendor_id: str
    event_id: Optional[str] = None


class NegotiationRequest(BaseModel):
    event_id: str
    vendor_id: str
    initial_offer: float = Field(gt=0)
    customer_target: Optional[float] = Field(default=None, gt=0)
    requested_discount_pct: Optional[float] = Field(default=None, ge=0, le=90)


class DecisionRequest(BaseModel):
    event_id: str
    vendor_id: str
    booking_id: Optional[str] = None
    request_id: Optional[str] = None
    quoted_price: float = Field(gt=0)
    category: str
    city: str
    attendee_count: int = Field(gt=0)
    start_at: datetime
    end_at: datetime


class CreateMilestoneInput(BaseModel):
    title: str
    amount: float = Field(gt=0)
    due_at: datetime
    sequence: int = Field(ge=1)


class EscrowBookingRequest(BaseModel):
    event_id: str
    user_id: str
    vendor_id: str
    total_amount: float = Field(gt=0)
    currency: str = "USD"
    milestones: List[CreateMilestoneInput] = Field(min_length=1, max_length=20)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReleaseMilestoneRequest(BaseModel):
    booking_id: str
    milestone_id: str
    actor_id: str
    actor_role: Literal["customer", "admin"]


class DecisionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    score: int
    explanation: List[str]
    risks: List[str]
    recommendation: Literal["book_now", "wait", "counter"]


class DecisionModelPerformanceResponse(BaseModel):
    current_model_version: int
    booking_prediction_accuracy: float
    dispute_prediction_accuracy: float
    average_score_error: float
    last_calibration_date: datetime
    calibration_failure_count: int
    last_aborted_reason: Optional[str] = None
    weight_stability_index: float
    model_age_days: float


class AIRollbackRequest(BaseModel):
    model_type: Literal["risk", "decision"]
    target_version: int = Field(ge=1)
