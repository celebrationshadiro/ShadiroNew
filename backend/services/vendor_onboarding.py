from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple


CATEGORY_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "grocery": {
        "label": "Grocery Vendors",
        "required": [
            "business_name",
            "owner_name",
            "city",
            "delivery_radius",
            "delivery_schedule",
            "product_catalog",
        ],
        "recommended": [
            "quality_grade",
            "minimum_order_quantity",
            "product_images",
        ],
        "notes": [
            "Catalog should include item name, category, unit price, stock status, and unit type.",
            "Delivery schedule can be time windows or days of the week.",
        ],
    },
    "venues": {
        "label": "Event Venues",
        "required": [
            "venue_name",
            "location",
            "capacity_min",
            "capacity_max",
            "venue_types",
            "pricing_model",
            "availability_calendar",
            "cancellation_policy",
        ],
        "recommended": [
            "amenities",
            "photo_gallery",
            "floor_plans",
            "virtual_tour",
        ],
        "notes": [
            "Capacity should include min and max guests.",
        ],
    },
    "wedding-planners": {
        "label": "Wedding Planners",
        "required": [
            "company_name",
            "experience_years",
            "services_offered",
            "package_tiers",
        ],
        "recommended": [
            "portfolio",
            "team_size",
            "specializations",
            "testimonials",
        ],
        "notes": [],
    },
    "makeup": {
        "label": "Makeup Artists & Stylists",
        "required": [
            "artist_name",
            "specializations",
            "service_menu",
            "pricing",
        ],
        "recommended": [
            "before_after_gallery",
            "products_used",
            "travel_charges",
            "trial_availability",
        ],
        "notes": [],
    },
    "photography": {
        "label": "Photographers & Videographers",
        "required": [
            "studio_name",
            "services",
            "packages",
            "delivery_timeline",
        ],
        "recommended": [
            "portfolio_gallery",
            "equipment_details",
            "raw_footage_policy",
        ],
        "notes": [],
    },
    "decor": {
        "label": "Decorators & Florists",
        "required": [
            "business_name",
            "specializations",
            "themes",
            "package_pricing",
        ],
        "recommended": [
            "service_catalog",
            "rental_items",
            "setup_dismantle",
            "customization",
        ],
        "notes": [],
    },
    "catering": {
        "label": "Caterers & Bakers",
        "required": [
            "business_name",
            "cuisine_specializations",
            "menu_items",
            "pricing_model",
            "dietary_options",
            "minimum_order_quantity",
        ],
        "recommended": [
            "service_style",
            "tasting_availability",
            "food_safety_certifications",
        ],
        "notes": [],
    },
    "entertainment": {
        "label": "DJs, Bands & Entertainers",
        "required": [
            "artist_name",
            "performance_type",
            "genres",
            "performance_packages",
        ],
        "recommended": [
            "equipment_included",
            "video_samples",
            "backup_artist",
        ],
        "notes": [],
    },
    "transport": {
        "label": "Transport & Rental Services",
        "required": [
            "company_name",
            "fleet_details",
            "vehicle_categories",
            "pricing_structure",
            "insurance_coverage",
        ],
        "recommended": [
            "decoration_services",
            "driver_included",
            "rental_duration_options",
        ],
        "notes": [],
    },
    "mehandi": {
        "label": "Mehandi Designers",
        "required": [
            "designer_name",
            "design_styles",
            "services",
            "pricing",
        ],
        "recommended": [
            "portfolio",
            "quality_type",
            "application_time_estimates",
            "home_service",
        ],
        "notes": [],
    },
}


CATEGORY_ID_TO_SLUG = {
    "cat-venues": "venues",
    "cat-wedding-planners": "wedding-planners",
    "cat-makeup": "makeup",
    "cat-photography": "photography",
    "cat-decor": "decor",
    "cat-catering": "catering",
    "cat-entertainment": "entertainment",
    "cat-transport": "transport",
    "cat-mehandi": "mehandi",
    "cat-grocery": "grocery",
}


def normalize_category_id(category_id: Optional[str]) -> Optional[str]:
    if not category_id:
        return None
    if category_id in CATEGORY_REQUIREMENTS:
        return category_id
    return CATEGORY_ID_TO_SLUG.get(category_id, category_id)


def build_profile_snapshot(payload: Dict[str, Any]) -> Dict[str, Any]:
    details = payload.get("details") or {}
    snapshot = {**payload, **details}
    # Normalize common aliases
    if "business_name" in payload and "venue_name" not in snapshot:
        snapshot["venue_name"] = payload.get("business_name")
    if "business_name" in payload and "company_name" not in snapshot:
        snapshot["company_name"] = payload.get("business_name")
    if "city" in payload and "location" not in snapshot:
        snapshot["location"] = payload.get("city")
    if "owner_name" in payload and "artist_name" not in snapshot:
        snapshot["artist_name"] = payload.get("owner_name")
    if "owner_name" in payload and "designer_name" not in snapshot:
        snapshot["designer_name"] = payload.get("owner_name")
    if "owner_name" in payload and "studio_name" not in snapshot:
        snapshot["studio_name"] = payload.get("owner_name")
    if "owner_name" in payload and "company_name" not in snapshot:
        snapshot["company_name"] = payload.get("owner_name")
    if "services_offered" in snapshot and "services" not in snapshot:
        snapshot["services"] = snapshot.get("services_offered")
    if ("price_min" in payload or "price_max" in payload) and "pricing" not in snapshot:
        if payload.get("price_min") or payload.get("price_max"):
            snapshot["pricing"] = {"min": payload.get("price_min"), "max": payload.get("price_max")}
    if "grocery_items" in snapshot and "product_catalog" not in snapshot:
        snapshot["product_catalog"] = snapshot.get("grocery_items")
    if "caterer_menu_items" in snapshot and "menu_items" not in snapshot:
        snapshot["menu_items"] = snapshot.get("caterer_menu_items")
    if "dj_equipment" in snapshot and "equipment_included" not in snapshot:
        snapshot["equipment_included"] = bool(snapshot.get("dj_equipment"))
    if "dj_packages" in snapshot and "performance_packages" not in snapshot:
        snapshot["performance_packages"] = snapshot.get("dj_packages")
    if "decorator_themes" in snapshot and "themes" not in snapshot:
        snapshot["themes"] = snapshot.get("decorator_themes")
    if "makeup_specializations" in snapshot and "specializations" not in snapshot:
        snapshot["specializations"] = snapshot.get("makeup_specializations")
    if "makeup_services" in snapshot and "service_menu" not in snapshot:
        snapshot["service_menu"] = snapshot.get("makeup_services")
    if "photo_services" in snapshot and "services" not in snapshot:
        snapshot["services"] = snapshot.get("photo_services")
    if "photo_packages" in snapshot and "packages" not in snapshot:
        snapshot["packages"] = snapshot.get("photo_packages")
    if "mehandi_services" in snapshot and "services" not in snapshot:
        snapshot["services"] = snapshot.get("mehandi_services")
    if "mehandi_pricing" in snapshot and "pricing" not in snapshot:
        snapshot["pricing"] = snapshot.get("mehandi_pricing")
    if "transport_vehicles" in snapshot and "fleet_details" not in snapshot:
        snapshot["fleet_details"] = snapshot.get("transport_vehicles")
    return snapshot


def validate_onboarding(payload: Dict[str, Any]) -> Dict[str, Any]:
    category_id = normalize_category_id(payload.get("category_id"))
    requirements = CATEGORY_REQUIREMENTS.get(category_id)
    snapshot = build_profile_snapshot(payload)

    if not requirements:
        return {
            "category": category_id,
            "label": "Unknown",
            "missing_required": [],
            "missing_recommended": [],
            "notes": ["No category-specific requirements available."],
            "status": "unknown",
        }

    missing_required = [field for field in requirements["required"] if not snapshot.get(field)]
    missing_recommended = [field for field in requirements["recommended"] if not snapshot.get(field)]
    status = "complete" if not missing_required else "incomplete"

    return {
        "category": category_id,
        "label": requirements.get("label"),
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "notes": requirements.get("notes", []),
        "status": status,
        "required": requirements.get("required", []),
        "recommended": requirements.get("recommended", []),
    }


def get_requirements(category_id: str) -> Dict[str, Any]:
    category_key = normalize_category_id(category_id)
    requirements = CATEGORY_REQUIREMENTS.get(category_key)
    if not requirements:
        return {
            "category": category_key,
            "label": "Unknown",
            "required": [],
            "recommended": [],
            "notes": ["No category-specific requirements available."],
        }
    return {
        "category": category_key,
        "label": requirements.get("label"),
        "required": requirements.get("required", []),
        "recommended": requirements.get("recommended", []),
        "notes": requirements.get("notes", []),
    }
