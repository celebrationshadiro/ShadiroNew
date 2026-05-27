"""Service booking routes: intent creation, vendor-pending, deprecated redirects."""
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from booking_engine.category_config import SERVICE_CATEGORIES, normalize_category_slug
from booking_engine.lock_service import acquire_slot_lock, utcnow as be_utcnow
from canonical_models.common import ResponseEnvelope, UserRole
from core.database import get_db_from_request
from core.settlement import SettlementService

from .helpers import (
    BookingListItem, ServiceIntentRequest, _audit_log, _compute_service_amount_paise,
    _normalize_role, _request_id, _resolve_vendor_id_for_user, _to_booking_list_item,
    _validate_service_category_meta, get_current_user, limiter,
)

router = APIRouter()


@router.post("/service/intent", response_model=ResponseEnvelope[dict])
async def create_service_booking_intent(
    request: Request,
    payload: ServiceIntentRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    role = _normalize_role(current_user.get("role"))
    if role != UserRole.CUSTOMER.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only customer can create service booking")

    category_slug = normalize_category_slug(payload.category_slug)
    if category_slug not in SERVICE_CATEGORIES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported service category")
    _validate_service_category_meta(category_slug, payload.category_meta or {})

    vendor = await db.vendors.find_one({"id": payload.vendor_id, "is_active": True}, {"_id": 0, "id": 1})
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found or inactive")

    existing = await db.service_bookings.find_one(
        {"idempotency_key": payload.idempotency_key, "customer_id": str(current_user.get("id"))},
        {"_id": 0},
    )
    if existing:
        return ResponseEnvelope[dict](
            success=True,
            data=existing,
            message="Idempotent replay",
            request_id=_request_id(request),
        )

    slot = await acquire_slot_lock(
        db,
        vendor_id=payload.vendor_id,
        date_value=payload.event_date,
        intent_id=payload.idempotency_key,
        ttl_min=30,
        start_time=payload.event_time,
        end_time=payload.event_time if payload.event_time.endswith(":59") else payload.event_time[:3] + "59",
    )
    now = be_utcnow()
    commission_bps = await SettlementService(db).get_commission_rate(payload.vendor_id, "service")
    amount, pricing_preview = await _compute_service_amount_paise(
        db,
        vendor_id=payload.vendor_id,
        package_id=payload.package_id,
        event_date=payload.event_date,
    )
    commission_paise = (amount * commission_bps) // 10000
    vendor_net = amount - commission_paise

    from uuid import uuid4
    service_booking = {
        "id": f"svc_{uuid4().hex}",
        "category_slug": category_slug,
        "customer_id": str(current_user.get("id")),
        "vendor_id": payload.vendor_id,
        "package_id": payload.package_id,
        "event_date": payload.event_date,
        "event_time": payload.event_time,
        "guest_count": int(payload.guest_count),
        "notes": payload.notes,
        "idempotency_key": payload.idempotency_key,
        "amount_paise": amount,
        "commission_rate_bps": commission_bps,
        "commission_paise": commission_paise,
        "vendor_net_paise": vendor_net,
        "payment_id": None,
        "status": "PENDING_VENDOR",
        "version": 1,
        "vendor_response_deadline": now + timedelta(hours=4),
        "vendor_response_at": None,
        "rejection_reason": None,
        "slot_lock_id": slot["lock_id"],
        "category_meta": {
            **(payload.category_meta or {}),
            "pricing_preview": pricing_preview,
        },
        "created_at": now,
        "updated_at": now,
    }
    await db.service_bookings.insert_one(service_booking)
    await _audit_log(
        db=db,
        actor_id=str(current_user.get("id")),
        actor_role=role,
        action="service_booking_created",
        entity_id=service_booking["id"],
        request_id=_request_id(request),
        payload={"vendor_id": payload.vendor_id, "amount_paise": amount, "category_slug": category_slug},
    )
    return ResponseEnvelope[dict](
        success=True,
        data=service_booking,
        message="Service booking created",
        request_id=_request_id(request),
    )


@router.get("/service/vendor/pending", response_model=ResponseEnvelope[list[BookingListItem]])
async def list_service_vendor_pending(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    role = _normalize_role(current_user.get("role"))
    if role not in {UserRole.VENDOR.value, UserRole.ADMIN.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vendor or admin only")

    query: dict[str, Any] = {"status": "PENDING_VENDOR"}
    if role == UserRole.VENDOR.value:
        vendor_id = await _resolve_vendor_id_for_user(db, current_user)
        query["vendor_id"] = vendor_id

    items = await db.service_bookings.find(query, {"_id": 0}).sort("created_at", -1).to_list(length=300)
    typed = [_to_booking_list_item(item) for item in items]
    return ResponseEnvelope[list[BookingListItem]](
        success=True,
        data=typed,
        message="Pending service bookings fetched",
        request_id=_request_id(request),
    )


# ── Deprecated redirect stubs ───────────────────────────────────────────────

@router.post("/service/{booking_id}/vendor-action", include_in_schema=False)
async def service_vendor_action_deprecated(booking_id: str):
    return RedirectResponse(
        url=f"/api/bookings/{booking_id}/action",
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
        headers={"Deprecation": "true"},
    )


@router.post("/service/{booking_id}/mark-progress", include_in_schema=False)
async def service_mark_progress_deprecated(booking_id: str):
    return RedirectResponse(
        url=f"/api/bookings/{booking_id}/action",
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
        headers={"Deprecation": "true"},
    )


@router.post("/service/{booking_id}/complete", include_in_schema=False)
async def service_complete_deprecated(booking_id: str):
    return RedirectResponse(
        url=f"/api/bookings/{booking_id}/action",
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
        headers={"Deprecation": "true"},
    )


@router.post("/service/{booking_id}/cancel", include_in_schema=False)
async def service_cancel_deprecated(booking_id: str):
    return RedirectResponse(
        url=f"/api/bookings/{booking_id}/action",
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
        headers={"Deprecation": "true"},
    )
