from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, ValidationError


CATEGORY_ALIASES: Dict[str, str] = {
    "caterer": "caterer",
    "catering": "caterer",
    "cat-catering": "caterer",
    "cat_catering": "caterer",
    "dj": "dj",
    "entertainment": "dj",
    "cat-entertainment": "dj",
    "cat_entertainment": "dj",
    "photographer": "photographer",
    "photography": "photographer",
    "cat-photography": "photographer",
    "cat_photography": "photographer",
    "venue": "venue",
    "venues": "venue",
    "cat-venues": "venue",
    "cat_venues": "venue",
    "decorator": "decorator",
    "decor": "decorator",
    "cat-decor": "decorator",
    "cat_decor": "decorator",
    "makeup_artist": "makeup_artist",
    "makeup": "makeup_artist",
    "cat-makeup": "makeup_artist",
    "cat_makeup": "makeup_artist",
    "mehendi_artist": "mehendi_artist",
    "mehandi_artist": "mehendi_artist",
    "mehendi": "mehendi_artist",
    "mehandi": "mehendi_artist",
    "cat-mehandi": "mehendi_artist",
    "cat_mehandi": "mehendi_artist",
    "cat-mehendi": "mehendi_artist",
    "cat_mehendi": "mehendi_artist",
    "band": "band",
    "event_planner": "event_planner",
    "planner": "event_planner",
    "wedding-planners": "event_planner",
    "wedding_planners": "event_planner",
    "cat-wedding-planners": "event_planner",
    "cat_wedding-planners": "event_planner",
    "transport": "transport",
    "cat-transport": "transport",
    "cat_transport": "transport",
}


class CategoryVendorProfileValidationError(Exception):
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(", ".join(errors))


class _BaseVendorDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DJVendorDetails(_BaseVendorDetails):
    performance_type: Optional[str] = None
    genres: Optional[List[str]] = None
    performance_packages: Optional[List[Dict[str, Any]]] = None
    equipment_included: Optional[bool] = None
    video_samples: Optional[List[str]] = None
    dj_equipment: Optional[List[Dict[str, Any]]] = None
    dj_packages: Optional[List[Dict[str, Any]]] = None
    dj_crew_size: Optional[int] = None
    availability_calendar: Optional[str] = None
    cancellation_policy: Optional[str] = None


class CatererVendorDetails(_BaseVendorDetails):
    cuisine_specializations: Optional[List[str]] = None
    menu_items: Optional[List[Dict[str, Any]]] = None
    dietary_options: Optional[List[str]] = None
    service_style: Optional[List[str]] = None
    tasting_availability: Optional[bool] = None
    food_safety_certifications: Optional[List[str]] = None
    pricing_model: Optional[str] = None
    minimum_order_quantity: Optional[float] = None
    caterer_menu_items: Optional[List[Dict[str, Any]]] = None
    caterer_price_per_plate: Optional[float] = None


class PhotographerVendorDetails(_BaseVendorDetails):
    services: Optional[List[str]] = None
    packages: Optional[List[Dict[str, Any]]] = None
    delivery_timeline: Optional[str] = None
    raw_footage_policy: Optional[str] = None
    portfolio_urls: Optional[List[str]] = None
    photo_services: Optional[List[str]] = None
    photo_packages: Optional[List[Dict[str, Any]]] = None
    equipment_details: Optional[List[str]] = None


class VenueVendorDetails(_BaseVendorDetails):
    venue_types: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    capacity_min: Optional[int] = None
    capacity_max: Optional[int] = None
    pricing_model: Optional[str] = None
    pricing_options: Optional[List[Dict[str, Any]]] = None
    availability_calendar: Optional[str] = None
    cancellation_policy: Optional[str] = None
    photo_gallery: Optional[List[str]] = None
    floor_plans: Optional[List[str]] = None
    virtual_tour_url: Optional[str] = None


class DecoratorVendorDetails(_BaseVendorDetails):
    themes: Optional[List[str]] = None
    rental_items: Optional[List[str]] = None
    specializations: Optional[List[str]] = None
    decorator_themes: Optional[List[Dict[str, Any]]] = None
    decorator_inventory: Optional[List[Dict[str, Any]]] = None
    decorator_setup_types: Optional[List[Dict[str, Any]]] = None


class MakeupVendorDetails(_BaseVendorDetails):
    specializations: Optional[List[str]] = None
    service_menu: Optional[List[Dict[str, Any]]] = None
    products_used: Optional[List[str]] = None
    travel_charges: Optional[str] = None
    trial_availability: Optional[bool] = None
    makeup_specializations: Optional[List[str]] = None
    makeup_services: Optional[List[Dict[str, Any]]] = None
    before_after_gallery: Optional[List[str]] = None
    home_service: Optional[bool] = None


class MehendiVendorDetails(_BaseVendorDetails):
    design_styles: Optional[List[str]] = None
    services: Optional[List[Dict[str, Any]]] = None
    pricing: Optional[Dict[str, Any]] = None
    quality_type: Optional[str] = None
    application_time_estimates: Optional[str] = None
    home_service: Optional[bool] = None
    mehandi_services: Optional[List[Dict[str, Any]]] = None
    mehandi_pricing: Optional[Dict[str, Any]] = None


class BandVendorDetails(_BaseVendorDetails):
    performance_type: Optional[str] = None
    genres: Optional[List[str]] = None
    performance_packages: Optional[List[Dict[str, Any]]] = None
    equipment_included: Optional[bool] = None
    video_samples: Optional[List[str]] = None


class EventPlannerVendorDetails(_BaseVendorDetails):
    services_offered: Optional[List[str]] = None
    package_tiers: Optional[List[str]] = None
    team_size: Optional[int] = None
    specializations: Optional[List[str]] = None
    portfolio_urls: Optional[List[str]] = None


class TransportVendorDetails(_BaseVendorDetails):
    transport_vehicles: Optional[List[Dict[str, Any]]] = None
    rental_duration_options: Optional[List[str]] = None
    driver_included: Optional[bool] = None


DETAILS_SCHEMA_MAP = {
    "dj": DJVendorDetails,
    "caterer": CatererVendorDetails,
    "photographer": PhotographerVendorDetails,
    "venue": VenueVendorDetails,
    "decorator": DecoratorVendorDetails,
    "makeup_artist": MakeupVendorDetails,
    "mehendi_artist": MehendiVendorDetails,
    "band": BandVendorDetails,
    "event_planner": EventPlannerVendorDetails,
    "transport": TransportVendorDetails,
}


def normalize_category_id(category_id: Optional[str]) -> Optional[str]:
    if not category_id:
        return None
    raw = str(category_id).strip().lower()
    if raw.startswith("cat-"):
        raw = raw[4:]
    elif raw.startswith("cat_"):
        raw = raw[4:]
    return CATEGORY_ALIASES.get(raw, raw)


def validate_and_normalize_vendor_details(category_id: Optional[str], details: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    normalized = normalize_category_id(category_id)
    payload = details or {}
    if not normalized:
        return payload
    schema = DETAILS_SCHEMA_MAP.get(normalized)
    if not schema:
        return payload
    try:
        validated = schema.model_validate(payload)
    except ValidationError as exc:
        errors = []
        for err in exc.errors():
            loc = ".".join(str(x) for x in err.get("loc", []))
            msg = err.get("msg", "Invalid value")
            errors.append(f"{loc}: {msg}" if loc else msg)
        raise CategoryVendorProfileValidationError(errors)
    return validated.model_dump(exclude_none=True)
