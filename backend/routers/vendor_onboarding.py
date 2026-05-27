"""Vendor onboarding completion endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from auth import require_role
from api.deps import get_db
from models import (
    VendorOnboardingDetailsUpdate,
    UserRole,
    resolve_vendor_detail_model,
    validate_vendor_details_for_category,
)
from services.category_vendor_profile import (
    CategoryVendorProfileValidationError,
    validate_and_normalize_vendor_details,
)
from services.vendor_onboarding import validate_onboarding
from services.vendor_type import resolve_vendor_type

router = APIRouter(prefix="/api/vendors", tags=["vendor-onboarding"])


@router.put("/{vendor_id}/onboarding")
async def update_vendor_onboarding(
    vendor_id: str,
    payload: VendorOnboardingDetailsUpdate,
    current_user: dict = Depends(require_role([UserRole.VENDOR, UserRole.ADMIN])),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    vendor_doc = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if not vendor_doc:
        raise HTTPException(status_code=404, detail="Vendor not found")

    is_owner = current_user.get("role") == UserRole.ADMIN or vendor_doc.get("user_id") == current_user.get("sub")
    if not is_owner:
        raise HTTPException(status_code=403, detail="Not authorized")

    model_cls = resolve_vendor_detail_model(vendor_doc.get("category_id"))
    if not model_cls:
        raise HTTPException(status_code=422, detail="No details schema configured for this category")

    if not isinstance(payload.details, model_cls):
        raise HTTPException(
            status_code=422,
            detail=f"details payload does not match category schema {model_cls.__name__}",
        )

    # Merge and validate strictly against the category-specific schema.
    details = dict(vendor_doc.get("details", {}) or {})
    details.update(payload.details.model_dump(exclude_none=True))
    try:
        typed_details = model_cls.model_validate(details)
        details = typed_details.model_dump(exclude_none=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid category details payload: {str(exc)}") from exc

    try:
        details = validate_and_normalize_vendor_details(vendor_doc.get("category_id"), details)
    except CategoryVendorProfileValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category-specific vendor details: {', '.join(exc.errors)}",
        ) from exc

    update_data = {"details": details}

    onboarding = validate_onboarding({
        "category_id": vendor_doc.get("category_id"),
        "business_name": update_data.get("business_name", vendor_doc.get("business_name")),
        "owner_name": update_data.get("owner_name", vendor_doc.get("owner_name")),
        "city": update_data.get("city", vendor_doc.get("city")),
        "location": update_data.get("location", vendor_doc.get("location")),
        "details": details,
        "price_min": update_data.get("price_min", vendor_doc.get("price_min")),
        "price_max": update_data.get("price_max", vendor_doc.get("price_max")),
    })

    update_data.update({
        "onboarding_status": onboarding.get("status"),
        "onboarding_missing_required": onboarding.get("missing_required", []),
        "onboarding_missing_recommended": onboarding.get("missing_recommended", []),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })

    await db.vendors.update_one({"id": vendor_id}, {"$set": update_data})
    updated = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})

    return {
        "vendor": updated,
        "onboarding": onboarding,
    }
