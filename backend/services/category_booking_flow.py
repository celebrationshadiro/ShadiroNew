from __future__ import annotations

from copy import deepcopy
from datetime import date, time
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, ValidationError


CATEGORY_ALIASES: Dict[str, str] = {
    "caterer": "caterer",
    "catering": "caterer",
    "dj": "dj",
    "photographer": "photographer",
    "venue": "venue",
    "decorator": "decorator",
    "makeup_artist": "makeup_artist",
    "makeup": "makeup_artist",
    "mehendi_artist": "mehendi_artist",
    "mehandi_artist": "mehendi_artist",
    "mehendi": "mehendi_artist",
    "mehandi": "mehendi_artist",
    "band": "band",
    "event_planner": "event_planner",
    "planner": "event_planner",
}


CATEGORY_BOOKING_FLOWS: Dict[str, Dict[str, Any]] = {
    "dj": {
        "flow_version": "v1",
        "advance_percentage": 30,
        "pricing_model": "package_plus_overtime",
        "booking_inputs": [
            {"key": "event_date", "label": "Event Date", "type": "date", "required": True},
            {"key": "start_time", "label": "Start Time", "type": "time", "required": True},
            {"key": "end_time", "label": "End Time", "type": "time", "required": True},
            {"key": "event_city", "label": "City", "type": "text", "required": True},
            {"key": "event_location", "label": "Venue / Locality", "type": "text", "required": True},
            {"key": "music_preference", "label": "Music Preference", "type": "text", "required": True},
        ],
    },
    "caterer": {
        "flow_version": "v1",
        "advance_percentage": 25,
        "pricing_model": "per_plate",
        "booking_inputs": [
            {"key": "event_date", "label": "Event Date", "type": "date", "required": True},
            {"key": "event_city", "label": "City", "type": "text", "required": True},
            {"key": "event_location", "label": "Venue / Locality", "type": "text", "required": True},
            {"key": "guest_count", "label": "Guest Count", "type": "number", "required": True},
            {"key": "service_style", "label": "Service Style", "type": "text", "required": True},
        ],
    },
    "photographer": {
        "flow_version": "v1",
        "advance_percentage": 30,
        "pricing_model": "package_based",
        "booking_inputs": [
            {"key": "event_date", "label": "Event Date", "type": "date", "required": True},
            {"key": "start_time", "label": "Start Time", "type": "time", "required": True},
            {"key": "event_city", "label": "City", "type": "text", "required": True},
            {"key": "event_location", "label": "Venue / Locality", "type": "text", "required": True},
            {"key": "coverage_type", "label": "Coverage Type", "type": "text", "required": True},
        ],
    },
    "venue": {
        "flow_version": "v1",
        "advance_percentage": 20,
        "pricing_model": "slot_based_fixed",
        "booking_inputs": [
            {"key": "event_date", "label": "Event Date", "type": "date", "required": True},
            {"key": "event_city", "label": "City", "type": "text", "required": True},
            {"key": "guest_count", "label": "Guest Count", "type": "number", "required": True},
            {"key": "slot", "label": "Slot", "type": "text", "required": True},
        ],
    },
    "decorator": {
        "flow_version": "v1",
        "advance_percentage": 40,
        "pricing_model": "package_plus_addons",
        "booking_inputs": [
            {"key": "event_date", "label": "Event Date", "type": "date", "required": True},
            {"key": "event_city", "label": "City", "type": "text", "required": True},
            {"key": "event_location", "label": "Venue / Locality", "type": "text", "required": True},
            {"key": "theme_style", "label": "Theme Style", "type": "text", "required": True},
        ],
    },
    "makeup_artist": {
        "flow_version": "v1",
        "advance_percentage": 30,
        "pricing_model": "per_person",
        "booking_inputs": [
            {"key": "event_date", "label": "Event Date", "type": "date", "required": True},
            {"key": "start_time", "label": "Ready By Time", "type": "time", "required": True},
            {"key": "event_city", "label": "City", "type": "text", "required": True},
            {"key": "service_mode", "label": "Home / Venue Service", "type": "text", "required": True},
        ],
    },
    "mehendi_artist": {
        "flow_version": "v1",
        "advance_percentage": 20,
        "pricing_model": "per_hand_plus_bridal",
        "booking_inputs": [
            {"key": "event_date", "label": "Event Date", "type": "date", "required": True},
            {"key": "start_time", "label": "Start Time", "type": "time", "required": True},
            {"key": "event_city", "label": "City", "type": "text", "required": True},
            {"key": "hands_count", "label": "Hands Count", "type": "number", "required": True},
        ],
    },
    "band": {
        "flow_version": "v1",
        "advance_percentage": 35,
        "pricing_model": "hour_plus_distance",
        "booking_inputs": [
            {"key": "event_date", "label": "Event Date", "type": "date", "required": True},
            {"key": "start_time", "label": "Start Time", "type": "time", "required": True},
            {"key": "route_start", "label": "Route Start", "type": "text", "required": True},
            {"key": "route_end", "label": "Route End", "type": "text", "required": True},
            {"key": "event_city", "label": "City", "type": "text", "required": True},
        ],
    },
    "event_planner": {
        "flow_version": "v1",
        "advance_percentage": 20,
        "pricing_model": "milestone_based",
        "booking_inputs": [
            {"key": "event_date", "label": "Primary Event Date", "type": "date", "required": True},
            {"key": "event_city", "label": "City", "type": "text", "required": True},
            {"key": "budget_range", "label": "Budget Range", "type": "text", "required": True},
            {"key": "event_scale", "label": "Event Scale", "type": "text", "required": True},
        ],
    },
}

class _BaseDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DJBookingDetails(_BaseDetails):
    event_date: date
    start_time: time
    end_time: Optional[time] = None
    event_city: str
    event_location: str
    music_preference: Literal["bollywood", "punjabi", "bhojpuri", "mix", "edm"]
    power_backup: Optional[Literal["yes", "no"]] = None


class CatererBookingDetails(_BaseDetails):
    event_date: date
    event_city: str
    event_location: str
    guest_count: int
    service_style: Literal["buffet", "plated", "live_counter"]


class PhotographerBookingDetails(_BaseDetails):
    event_date: date
    start_time: time
    event_city: str
    event_location: str
    coverage_type: Literal["candid_plus_traditional", "candid_only", "video_only"]
    deliverable_priority: Optional[Literal["album_and_reels", "reels_fast", "raw_delivery"]] = None


class VenueBookingDetails(_BaseDetails):
    event_date: date
    event_city: str
    guest_count: int
    slot: Literal["morning", "evening", "full_day"]
    parking_needed: Optional[Literal["yes", "no"]] = None


class DecoratorBookingDetails(_BaseDetails):
    event_date: date
    event_city: str
    event_location: str
    theme_style: Literal["floral", "minimal", "royal"]
    setup_hours: Optional[int] = None


class MakeupBookingDetails(_BaseDetails):
    event_date: date
    start_time: time
    event_city: str
    service_mode: Literal["home", "venue"]
    people_count: Optional[int] = None


class MehendiBookingDetails(_BaseDetails):
    event_date: date
    start_time: time
    event_city: str
    hands_count: int
    design_level: Optional[Literal["simple", "arabic", "bridal_heavy"]] = None


class BandBookingDetails(_BaseDetails):
    event_date: date
    start_time: time
    route_start: str
    route_end: str
    event_city: str
    route_km: Optional[int] = None


class EventPlannerBookingDetails(_BaseDetails):
    event_date: date
    event_city: str
    budget_range: Literal["50000-200000", "200000-500000", "500000+"]
    event_scale: Literal["small", "mid", "large"]


DETAILS_SCHEMA_MAP = {
    "dj": DJBookingDetails,
    "caterer": CatererBookingDetails,
    "photographer": PhotographerBookingDetails,
    "venue": VenueBookingDetails,
    "decorator": DecoratorBookingDetails,
    "makeup_artist": MakeupBookingDetails,
    "mehendi_artist": MehendiBookingDetails,
    "band": BandBookingDetails,
    "event_planner": EventPlannerBookingDetails,
}

class CategoryBookingValidationError(Exception):
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(", ".join(errors))


def normalize_category_id(category_id: Optional[str]) -> Optional[str]:
    if not category_id:
        return None
    return CATEGORY_ALIASES.get(str(category_id).strip().lower(), str(category_id).strip().lower())


def get_booking_flow_template(category_id: Optional[str]) -> Optional[Dict[str, Any]]:
    normalized = normalize_category_id(category_id)
    if not normalized:
        return None
    template = CATEGORY_BOOKING_FLOWS.get(normalized)
    if not template:
        return None
    out = deepcopy(template)
    out["category_id"] = normalized
    return out


def validate_booking_details(category_id: Optional[str], details: Optional[Dict[str, Any]]) -> List[str]:
    template = get_booking_flow_template(category_id)
    if not template:
        return []
    payload = details or {}
    missing: List[str] = []
    for field in template.get("booking_inputs", []):
        if not field.get("required"):
            continue
        key = field.get("key")
        value = payload.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(key)
    return missing


def validate_and_normalize_booking_details(
    category_id: Optional[str], details: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    normalized = normalize_category_id(category_id)
    if not normalized:
        return details or {}
    schema = DETAILS_SCHEMA_MAP.get(normalized)
    if not schema:
        return details or {}

    payload = details or {}
    try:
        validated = schema.model_validate(payload)
    except ValidationError as exc:
        errors = []
        for err in exc.errors():
            loc = ".".join(str(x) for x in err.get("loc", []))
            msg = err.get("msg", "Invalid value")
            errors.append(f"{loc}: {msg}" if loc else msg)
        raise CategoryBookingValidationError(errors)

    return validated.model_dump(mode="json")


def build_payment_plan(total_amount: float, category_id: Optional[str]) -> Dict[str, Any]:
    template = get_booking_flow_template(category_id) or {}
    advance_pct = int(template.get("advance_percentage", 30))
    advance_amount = round(float(total_amount or 0) * advance_pct / 100, 2)
    remaining_amount = round(float(total_amount or 0) - advance_amount, 2)
    return {
        "advance_percentage": advance_pct,
        "advance_amount": advance_amount,
        "remaining_amount": remaining_amount,
        "escrow_enabled": True,
        "pricing_model": template.get("pricing_model", "custom"),
    }
