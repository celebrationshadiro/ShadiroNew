"""Typed vendor registration router with secure user+vendor creation."""
from __future__ import annotations

from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from api.deps import get_db
from canonical_models.common import ResponseEnvelope, UserRole, utcnow
from core.config import get_settings
from core.security import hash_password
from routers.auth import AuthPayload, AuthUser, _issue_token_pair

router = APIRouter(prefix="/api", tags=["vendor-registration"])
settings = get_settings()


class VendorRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: Optional[str] = None
    business_name: str = Field(min_length=2, max_length=200)
    category_id: str
    city: Optional[str] = None
    description: Optional[str] = None


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


@router.post("/vendor-register", response_model=ResponseEnvelope[AuthPayload])
async def vendor_register(
    request: Request,
    payload: VendorRegisterRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    existing_user = await db.users.find_one({"email": payload.email.lower().strip()}, {"_id": 0, "id": 1})
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    now = utcnow()
    user_id = f"usr_{uuid4().hex}"
    vendor_id = f"ven_{uuid4().hex}"

    user_doc = {
        "id": user_id,
        "email": payload.email.lower().strip(),
        "name": payload.name.strip(),
        "phone": payload.phone,
        "role": UserRole.VENDOR.value,
        "password_hash": hash_password(payload.password),
        "is_active": True,
        "is_blocked": False,
        "created_at": now,
        "updated_at": now,
    }
    await db.users.insert_one(user_doc)

    vendor_doc = {
        "id": vendor_id,
        "user_id": user_id,
        "business_name": payload.business_name.strip(),
        "category_id": payload.category_id,
        "vendor_type": "service_vendor",
        "city": payload.city,
        "location": payload.city,
        "description": payload.description,
        "status": "PENDING",
        "subscription_plan": "free",
        "is_featured": False,
        "is_active": True,
        "rating": 0.0,
        "total_reviews": 0,
        "is_verified": False,
        "verification_status": "pending",
        "service_areas": [],
        "media": [],
        "pricing_rules": [],
        "details": {},
        "created_at": now,
        "updated_at": now,
        "onboarding_status": "pending",
        "onboarding_missing_required": [],
        "onboarding_missing_recommended": [],
    }
    await db.vendors.insert_one(vendor_doc)

    access_token, refresh_token = await _issue_token_pair(
        db=db,
        user_id=user_id,
        role=UserRole.VENDOR,
        request=request,
    )
    auth_user = AuthUser(
        id=user_id,
        name=user_doc["name"],
        email=user_doc["email"],
        phone=user_doc["phone"],
        role=UserRole.VENDOR.value,
        is_active=True,
        is_blocked=False,
        created_at=now,
        updated_at=now,
    )
    auth_payload = AuthPayload(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=auth_user,
    )
    return ResponseEnvelope[AuthPayload](
        success=True,
        data=auth_payload,
        message="Vendor registration successful",
        request_id=_request_id(request),
    )
