"""Vendor domain models: categories, details, registration, onboarding."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TypeAlias

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from .shared_models import MediaAsset, PackageTier


# --- Vendor enums (owned by vendor domain) ---
class VendorType(str, Enum):
    SERVICE_VENDOR = "service_vendor"
    PRODUCT_VENDOR = "product_vendor"


class VendorStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SUSPENDED = "suspended"
    REJECTED = "rejected"


class SubscriptionPlan(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# --- Category model ---
class VendorCategory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    image_url: Optional[str] = None


# --- Category-specific item models ---
class GroceryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: Optional[str] = None
    unit: str = "kg"
    unit_price: float
    availability: str = "in_stock"
    quality_grade: Optional[str] = None
    minimum_order_quantity: Optional[float] = None
    image_url: Optional[str] = None


class DJEquipmentItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    included: bool = True
    unit_price: Optional[float] = None


class DJPackage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    duration_hours: int
    price: float
    includes: List[str] = []


class CatererMenuItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: Optional[str] = None
    unit_price: float
    dietary_options: List[str] = []
    is_available: bool = True


class DecorTheme(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    price: Optional[float] = None


class DecorInventoryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: Optional[str] = None
    rental_price: Optional[float] = None
    quantity: Optional[int] = None


class DecorSetupType(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    included: bool = True
    price: Optional[float] = None


class VenuePricingOption(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    label: str
    unit: str = "per_day"
    price: float


class MakeupService(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    price: float


class PhotoPackage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    hours: int
    price: float
    deliverables: List[str] = []


class TransportVehicle(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: Optional[str] = None
    capacity: Optional[int] = None
    price: Optional[float] = None
    unit: str = "per_day"


class MehandiService(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    price: float
    unit: str = "per_hand"


# --- Vendor detail composites ---
class DJVendorDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dj_equipment: Optional[List[DJEquipmentItem]] = None
    dj_packages: Optional[List[DJPackage]] = None
    dj_crew_size: Optional[int] = None


class CatererDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    caterer_menu_items: Optional[List[CatererMenuItem]] = None
    caterer_price_per_plate: Optional[float] = None


class DecoratorDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decorator_themes: Optional[List[DecorTheme]] = None
    decorator_inventory: Optional[List[DecorInventoryItem]] = None
    decorator_setup_types: Optional[List[DecorSetupType]] = None


class VenueDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    venue_types: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    capacity_min: Optional[int] = None
    capacity_max: Optional[int] = None
    pricing_model: Optional[str] = None
    pricing_options: Optional[List[VenuePricingOption]] = None
    virtual_tour_url: Optional[str] = None


class MakeupDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    makeup_specializations: Optional[List[str]] = None
    makeup_services: Optional[List[MakeupService]] = None
    before_after_gallery: Optional[List[str]] = None


class PhotographerDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    photo_services: Optional[List[str]] = None
    photo_packages: Optional[List[PhotoPackage]] = None
    equipment_details: Optional[List[str]] = None


class TransportDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    transport_vehicles: Optional[List[TransportVehicle]] = None
    rental_duration_options: Optional[List[str]] = None
    driver_included: Optional[bool] = None


class MehandiDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mehandi_services: Optional[List[MehandiService]] = None
    mehandi_pricing: Optional[Dict[str, Any]] = None


class GroceryDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grocery_items: Optional[List[GroceryItem]] = None


VendorDetailsModel: TypeAlias = (
    DJVendorDetails
    | CatererDetails
    | DecoratorDetails
    | VenueDetails
    | MakeupDetails
    | PhotographerDetails
    | TransportDetails
    | MehandiDetails
    | GroceryDetails
)


# --- Base vendor models ---
class VendorBase(BaseModel):
    business_name: str
    category_id: str
    vendor_type: VendorType = VendorType.SERVICE_VENDOR
    commission_percentage: Optional[float] = None
    minimum_commission: Optional[float] = None
    description: Optional[str] = None
    location: Optional[str] = None
    city: Optional[str] = None
    base_price: Optional[float] = None
    rating: float = 0.0
    total_reviews: int = 0
    is_verified: bool = False
    pricing_rules: List[Dict[str, Any]] = []
    verification_status: Optional[str] = None
    verification_documents: List[Dict[str, Any]] = []


class VendorCreate(VendorBase):
    pass


class VendorCreateRequest(BaseModel):
    business_name: str
    category_id: str
    vendor_type: VendorType = VendorType.SERVICE_VENDOR
    description: Optional[str] = None
    location: Optional[str] = None
    city: Optional[str] = None
    base_price: Optional[float] = None
    pricing_rules: List[Dict[str, Any]] = []
    verification_documents: List[Dict[str, Any]] = []
    service_areas: List[str] = []


class VendorAdminPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    commission_percentage: Optional[float] = None
    minimum_commission: Optional[float] = None
    is_featured: Optional[bool] = None
    subscription_plan: Optional[SubscriptionPlan] = None


class BaseVendor(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    business_name: str
    category_id: str
    vendor_type: VendorType = VendorType.SERVICE_VENDOR
    city: Optional[str] = None
    location: Optional[str] = None
    base_price: Optional[float] = None
    rating: float = 0.0
    total_reviews: int = 0
    is_verified: bool = False
    status: VendorStatus = VendorStatus.PENDING
    subscription_plan: SubscriptionPlan = SubscriptionPlan.FREE
    description: Optional[str] = None
    service_areas: List[str] = []
    media: List[MediaAsset] = []
    pricing_rules: List[Dict[str, Any]] = []
    onboarding_status: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VendorWithDetails(BaseVendor):
    details: VendorDetailsModel | None = None


def resolve_vendor_detail_model(category_id: Optional[str]):
    normalized = str(category_id or "").strip().lower()
    if not normalized:
        return None
    if "grocery" in normalized:
        return GroceryDetails
    if "dj" in normalized:
        return DJVendorDetails
    if "cater" in normalized:
        return CatererDetails
    if "decor" in normalized:
        return DecoratorDetails
    if "venue" in normalized or "hall" in normalized:
        return VenueDetails
    if "makeup" in normalized:
        return MakeupDetails
    if "photo" in normalized or "video" in normalized:
        return PhotographerDetails
    if "transport" in normalized or "car" in normalized:
        return TransportDetails
    if "mehandi" in normalized or "mehendi" in normalized:
        return MehandiDetails
    return None


def validate_vendor_details_for_category(category_id: Optional[str], details: Dict[str, Any]) -> VendorDetailsModel | None:
    if not details:
        return None
    model_cls = resolve_vendor_detail_model(category_id)
    if not model_cls:
        return None
    return model_cls.model_validate(details)


class Vendor(VendorBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    owner_name: Optional[str] = None
    phone: Optional[str] = None
    service_areas: List[str] = []
    years_of_experience: Optional[int] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    highlights: List[str] = []
    profile_image_url: Optional[str] = None
    portfolio_urls: List[str] = []
    status: VendorStatus = VendorStatus.PENDING
    subscription_plan: SubscriptionPlan = SubscriptionPlan.FREE
    is_featured: bool = False
    media: List[MediaAsset] = []
    services: List[str] = []
    details: Dict[str, Any] = {}
    grocery_items: List[GroceryItem] = []
    dj_equipment: List[DJEquipmentItem] = []
    dj_packages: List[DJPackage] = []
    dj_crew_size: Optional[int] = None
    caterer_menu_items: List[CatererMenuItem] = []
    caterer_price_per_plate: Optional[float] = None
    decorator_themes: List[DecorTheme] = []
    decorator_inventory: List[DecorInventoryItem] = []
    decorator_setup_types: List[DecorSetupType] = []
    venue_types: List[str] = []
    amenities: List[str] = []
    capacity_min: Optional[int] = None
    capacity_max: Optional[int] = None
    pricing_model: Optional[str] = None
    pricing_options: List[VenuePricingOption] = []
    availability_calendar: Optional[str] = None
    cancellation_policy: Optional[str] = None
    photo_gallery: List[str] = []
    floor_plans: List[str] = []
    virtual_tour_url: Optional[str] = None
    makeup_specializations: List[str] = []
    makeup_services: List[MakeupService] = []
    before_after_gallery: List[str] = []
    photo_services: List[str] = []
    photo_packages: List[PhotoPackage] = []
    equipment_details: List[str] = []
    transport_vehicles: List[TransportVehicle] = []
    rental_duration_options: List[str] = []
    driver_included: Optional[bool] = None
    decoration_services: Optional[bool] = None
    mehandi_services: List[MehandiService] = []
    mehandi_pricing: Dict[str, Any] = {}
    onboarding_status: Optional[str] = None
    onboarding_missing_required: List[str] = []
    onboarding_missing_recommended: List[str] = []
    accepted_count: int = 0
    rejected_count: int = 0
    completed_count: int = 0
    emergency_count: int = 0
    acceptance_rate: float = 0.0
    reliability_score: float = 100.0
    visibility_score: float = 1.0
    is_available: bool = True
    availability_note: Optional[str] = None
    next_available_date: Optional[str] = None
    vendor_payout_balance: float = 0.0
    withdrawn_amount: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VendorRegistration(BaseModel):
    business_name: str
    owner_name: str
    email: EmailStr
    phone: str = Field(pattern=r"^\d{10}$")
    password: str = Field(min_length=8, max_length=128)
    category_id: str
    city: str
    service_areas: List[str] = []
    years_of_experience: Optional[int] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    description: Optional[str] = None
    highlights: List[str] = []
    delivery_radius: Optional[str] = None
    delivery_schedule: Optional[str] = None
    product_catalog: Optional[List[Dict[str, Any]]] = None
    minimum_order_quantity: Optional[float] = None
    quality_grade: Optional[str] = None
    venue_types: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    capacity_min: Optional[int] = None
    capacity_max: Optional[int] = None
    pricing_model: Optional[str] = None
    availability_calendar: Optional[str] = None
    cancellation_policy: Optional[str] = None
    portfolio_urls: Optional[List[str]] = None
    services_offered: Optional[List[str]] = None
    package_tiers: Optional[List[str]] = None
    team_size: Optional[int] = None
    specializations: Optional[List[str]] = None
    service_menu: Optional[List[Dict[str, Any]]] = None
    products_used: Optional[List[str]] = None
    travel_charges: Optional[str] = None
    trial_availability: Optional[bool] = None
    packages: Optional[List[Dict[str, Any]]] = None
    delivery_timeline: Optional[str] = None
    raw_footage_policy: Optional[str] = None
    themes: Optional[List[str]] = None
    rental_items: Optional[List[str]] = None
    cuisine_specializations: Optional[List[str]] = None
    menu_items: Optional[List[Dict[str, Any]]] = None
    dietary_options: Optional[List[str]] = None
    service_style: Optional[List[str]] = None
    tasting_availability: Optional[bool] = None
    food_safety_certifications: Optional[List[str]] = None
    performance_type: Optional[str] = None
    genres: Optional[List[str]] = None
    performance_packages: Optional[List[Dict[str, Any]]] = None
    equipment_included: Optional[bool] = None
    video_samples: Optional[List[str]] = None
    fleet_details: Optional[List[Dict[str, Any]]] = None
    vehicle_categories: Optional[List[str]] = None
    pricing_structure: Optional[str] = None
    insurance_coverage: Optional[str] = None
    design_styles: Optional[List[str]] = None
    application_time_estimates: Optional[str] = None
    home_service: Optional[bool] = None
    details: Dict[str, Any] = {}
    grocery_items: Optional[List[GroceryItem]] = None
    dj_equipment: Optional[List[DJEquipmentItem]] = None
    dj_packages: Optional[List[DJPackage]] = None
    dj_crew_size: Optional[int] = None
    caterer_menu_items: Optional[List[CatererMenuItem]] = None
    caterer_price_per_plate: Optional[float] = None
    decorator_themes: Optional[List[DecorTheme]] = None
    decorator_inventory: Optional[List[DecorInventoryItem]] = None
    decorator_setup_types: Optional[List[DecorSetupType]] = None
    pricing_rules: Optional[List[Dict[str, Any]]] = None
    pricing_options: Optional[List[VenuePricingOption]] = None
    photo_gallery: Optional[List[str]] = None
    floor_plans: Optional[List[str]] = None
    virtual_tour_url: Optional[str] = None
    makeup_specializations: Optional[List[str]] = None
    makeup_services: Optional[List[MakeupService]] = None
    before_after_gallery: Optional[List[str]] = None
    photo_services: Optional[List[str]] = None
    photo_packages: Optional[List[PhotoPackage]] = None
    equipment_details: Optional[List[str]] = None
    transport_vehicles: Optional[List[TransportVehicle]] = None
    rental_duration_options: Optional[List[str]] = None
    driver_included: Optional[bool] = None
    decoration_services: Optional[bool] = None
    mehandi_services: Optional[List[MehandiService]] = None
    mehandi_pricing: Optional[Dict[str, Any]] = None
    onboarding_status: Optional[str] = None
    onboarding_missing_required: List[str] = []
    onboarding_missing_recommended: List[str] = []


class VendorOnboardingUpdate(BaseModel):
    """Payload for onboarding update/patch."""
    business_name: Optional[str] = None
    owner_name: Optional[str] = None
    city: Optional[str] = None
    service_areas: Optional[List[str]] = None
    delivery_radius: Optional[str] = None
    delivery_schedule: Optional[str] = None
    product_catalog: Optional[List[Dict[str, Any]]] = None
    services_offered: Optional[List[str]] = None
    capacity_min: Optional[int] = None
    capacity_max: Optional[int] = None
    venue_types: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    pricing_model: Optional[str] = None
    pricing_options: Optional[List[Dict[str, Any]]] = None
    dj_equipment: Optional[List[DJEquipmentItem]] = None
    dj_packages: Optional[List[DJPackage]] = None
    caterer_menu_items: Optional[List[CatererMenuItem]] = None
    caterer_price_per_plate: Optional[float] = None
    decorator_themes: Optional[List[DecorTheme]] = None
    decorator_inventory: Optional[List[DecorInventoryItem]] = None
    decorator_setup_types: Optional[List[DecorSetupType]] = None
    makeup_services: Optional[List[MakeupService]] = None
    photo_packages: Optional[List[PhotoPackage]] = None
    transport_vehicles: Optional[List[TransportVehicle]] = None
    mehandi_services: Optional[List[MehandiService]] = None
    onboarding_status: Optional[str] = None
    onboarding_missing_required: Optional[List[str]] = None
    onboarding_missing_recommended: Optional[List[str]] = None
    details: Optional[Dict[str, Any]] = None


class VendorOnboardingDetailsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    details: VendorDetailsModel
