"""Rental booking routes: availability, intent, pay-balance, cancel."""
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pymongo import ReturnDocument

from booking_engine.lock_service import acquire_date_range_lock, release_lock
from canonical_models.common import BookingIntentStatus, BookingStatus, ResponseEnvelope, UserRole, utcnow
from core.database import get_db_from_request

from .helpers import (
    RentalAvailabilityResponse, RentalCancelRequest, RentalIntentRequest, RentalPayBalanceRequest,
    _audit_log, _compute_rental_deposit, _enforce_booking_access, _fetch_booking_or_404,
    _lookup_rental_daily_base_price_paise, _normalize_role, _parse_date_string, _payment_client_from_app,
    _rental_days_inclusive, _rental_refund_amounts, _request_id, get_current_user, limiter, settings,
)

router = APIRouter()


@router.get("/rental/availability/{item_id}", response_model=ResponseEnvelope[RentalAvailabilityResponse])
async def rental_availability(
    item_id: str,
    request: Request,
    check_in: str = Query(...),
    check_out: str = Query(...),
):
    db = get_db_from_request(request)
    check_in_date = _parse_date_string(check_in)
    check_out_date = _parse_date_string(check_out)
    if check_in_date > check_out_date:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="check_in after check_out")

    conflicts = await db.bookings.find(
        {
            "category_type": "rental",
            "meta.item_id": item_id,
            "status": {"$nin": ["CANCELLED", "REFUNDED"]},
            "meta.check_in_date": {"$lte": check_out_date},
            "meta.check_out_date": {"$gte": check_in_date},
        },
        {"_id": 0, "meta.check_in_date": 1, "meta.check_out_date": 1},
    ).to_list(length=200)

    conflicting_dates = []
    for c in conflicts:
        meta = c.get("meta") or {}
        if meta.get("check_in_date") and meta.get("check_out_date"):
            conflicting_dates.append(f"{meta.get('check_in_date')}:{meta.get('check_out_date')}")

    return ResponseEnvelope[RentalAvailabilityResponse](
        success=True,
        data=RentalAvailabilityResponse(
            available=len(conflicting_dates) == 0,
            conflicting_dates=conflicting_dates,
        ),
        message="Availability checked",
        request_id=_request_id(request),
    )


@router.post("/rental/intent", response_model=ResponseEnvelope[dict])
async def create_rental_booking_intent(
    request: Request,
    payload: RentalIntentRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    role = _normalize_role(current_user.get("role"))
    if role != UserRole.CUSTOMER.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only customer can create rental booking")

    check_in_date = _parse_date_string(payload.check_in_date)
    check_out_date = _parse_date_string(payload.check_out_date)
    if check_in_date > check_out_date:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="check_in after check_out")

    existing = await db.bookings.find_one({"idempotency_key": payload.idempotency_key}, {"_id": 0})
    if existing:
        return ResponseEnvelope[dict](
            success=True,
            data=existing,
            message="Idempotent replay",
            request_id=_request_id(request),
        )

    conflicts = await db.bookings.find(
        {
            "category_type": "rental",
            "meta.item_id": payload.item_id,
            "status": {"$nin": ["CANCELLED", "REFUNDED"]},
            "meta.check_in_date": {"$lte": check_out_date},
            "meta.check_out_date": {"$gte": check_in_date},
        },
        {"_id": 0},
    ).to_list(length=1)
    if conflicts:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Selected date range is not available")

    active_locks = await db.resource_locks.find(
        {
            "entity_type": "DATE_RANGE",
            "entity_id": payload.item_id,
            "status": "ACTIVE",
            "metadata.check_in": {"$lte": check_out_date},
            "metadata.check_out": {"$gte": check_in_date},
        },
        {"_id": 0, "id": 1},
    ).to_list(length=1)
    if active_locks:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Selected date range is temporarily locked")

    now = utcnow()
    lock = await acquire_date_range_lock(
        db,
        item_id=payload.item_id,
        check_in=check_in_date,
        check_out=check_out_date,
        intent_id=payload.idempotency_key,
        ttl_min=20,
    )
    rental_days = _rental_days_inclusive(check_in_date, check_out_date)
    daily_base_price_paise, rental_item_title = await _lookup_rental_daily_base_price_paise(
        db,
        vendor_id=payload.vendor_id,
        item_id=payload.item_id,
    )
    total_amount_paise = int(daily_base_price_paise * rental_days)
    if total_amount_paise <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid computed rental amount")
    deposit_paise, balance_paise = _compute_rental_deposit(total_amount_paise)

    intent_id = f"bint_{uuid4().hex}"
    balance_due_at = None
    try:
        balance_due_at = datetime.fromisoformat(f"{check_in_date}T00:00:00+05:30").astimezone(tz=utcnow().tzinfo) - timedelta(days=3)
    except Exception:
        balance_due_at = None

    intent_doc = {
        "id": intent_id,
        "idempotency_key": payload.idempotency_key,
        "user_id": str(current_user.get("id")),
        "vendor_id": payload.vendor_id,
        "category_type": "rental",
        "items": [
            {
                "item_id": payload.item_id,
                "title": rental_item_title,
                "qty": rental_days,
                "unit_price_paise": daily_base_price_paise,
                "total_price_paise": total_amount_paise,
                "meta": payload.category_meta or {},
            }
        ],
        "total_amount_paise": total_amount_paise,
        "scheduled_at": None,
        "duration_minutes": None,
        "notes": payload.notes,
        "meta": {
            "item_id": payload.item_id,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "rental_days": rental_days,
            "daily_base_price_paise": daily_base_price_paise,
            "deposit_amount_paise": deposit_paise,
            "balance_amount_paise": balance_paise,
            "category_slug": payload.category_slug,
            "date_lock_id": lock.get("lock_id"),
            "lock_expires_at": lock.get("expires_at"),
            "balance_due_at": balance_due_at,
            "balance_reminded": False,
            **(payload.category_meta or {}),
        },
        "status": BookingIntentStatus.PENDING.value,
        "expires_at": now + timedelta(minutes=30),
        "created_at": now,
        "updated_at": now,
        "version": 1,
    }
    await db.booking_intents.insert_one(intent_doc)

    booking_id = f"book_{uuid4().hex}"
    booking_doc = {
        "id": booking_id,
        "intent_id": intent_id,
        "user_id": intent_doc["user_id"],
        "vendor_id": intent_doc["vendor_id"],
        "category_type": "rental",
        "items": intent_doc["items"],
        "status": BookingStatus.AWAITING_PAYMENT.value,
        "version": 1,
        "scheduled_at": None,
        "duration_minutes": None,
        "amount_gross_paise": total_amount_paise,
        "commission_rate_bps": 0,
        "commission_amount_paise": 0,
        "vendor_net_paise": total_amount_paise,
        "payment_id": None,
        "resource_lock_ids": [lock.get("lock_id")],
        "notes": payload.notes,
        "meta": intent_doc["meta"],
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
        "cancelled_at": None,
        "idempotency_key": payload.idempotency_key,
    }
    await db.bookings.insert_one(booking_doc)

    razorpay_client = _payment_client_from_app(request)
    razorpay_order = razorpay_client.order.create(
        {
            "amount": deposit_paise,
            "currency": "INR",
            "receipt": intent_id,
            "notes": {"booking_intent_id": intent_id, "booking_id": booking_id, "category_type": "rental"},
        }
    )

    payment_doc = {
        "id": f"pay_{uuid4().hex}",
        "booking_intent_id": intent_id,
        "booking_id": booking_id,
        "amount": deposit_paise,
        "currency": "INR",
        "status": "CREATED",
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_payment_id": None,
        "razorpay_signature": None,
        "idempotency_key": f"{intent_id}:{razorpay_order['id']}",
        "created_at": now,
        "updated_at": now,
    }
    await db.payments.insert_one(payment_doc)

    response_payload = {
        "id": booking_id,
        "booking_id": booking_id,
        "intent_id": intent_id,
        "status": booking_doc["status"],
        "payment": {
            "razorpay_order_id": razorpay_order["id"],
            "order_id": razorpay_order["id"],
            "amount_paise": deposit_paise,
            "currency": "INR",
            "key_id": settings.RAZORPAY_KEY_ID,
        },
    }
    return ResponseEnvelope[dict](
        success=True,
        data=response_payload,
        message="Rental booking created",
        request_id=_request_id(request),
    )


@router.post("/rental/{booking_id}/pay-balance", response_model=ResponseEnvelope[dict])
async def pay_rental_balance(
    booking_id: str,
    request: Request,
    payload: RentalPayBalanceRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    booking = await _fetch_booking_or_404(db, booking_id)
    await _enforce_booking_access(request, booking, current_user)

    if booking.get("category_type") != "rental":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a rental booking")

    meta = booking.get("meta") or {}
    balance_paise = int(meta.get("balance_amount_paise", 0) or 0)
    if balance_paise <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No balance due")

    razorpay_client = _payment_client_from_app(request)
    razorpay_order = razorpay_client.order.create(
        {
            "amount": balance_paise,
            "currency": "INR",
            "receipt": booking_id,
            "notes": {"booking_id": booking_id, "category_type": "rental", "payment_stage": "balance"},
        }
    )

    payment_doc = {
        "id": f"pay_{uuid4().hex}",
        "booking_intent_id": booking.get("intent_id"),
        "booking_id": booking_id,
        "amount": balance_paise,
        "currency": "INR",
        "status": "CREATED",
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_payment_id": None,
        "razorpay_signature": None,
        "idempotency_key": f"{booking_id}:{razorpay_order['id']}",
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    await db.payments.insert_one(payment_doc)

    return ResponseEnvelope[dict](
        success=True,
        data={
            "booking_id": booking_id,
            "razorpay_order_id": razorpay_order["id"],
            "amount_paise": balance_paise,
            "currency": "INR",
            "key_id": settings.RAZORPAY_KEY_ID,
        },
        message="Balance payment order created",
        request_id=_request_id(request),
    )


@router.post("/rental/{booking_id}/cancel", response_model=ResponseEnvelope[dict])
async def cancel_rental_booking(
    booking_id: str,
    payload: RentalCancelRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    booking = await _fetch_booking_or_404(db, booking_id)
    await _enforce_booking_access(request, booking, current_user)

    if booking.get("category_type") != "rental":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a rental booking")

    current_status = str(booking.get("status") or "")
    if current_status in {"CANCELLED", "COMPLETED"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cancellation not allowed in current status")

    updated = await db.bookings.find_one_and_update(
        {"id": booking_id, "version": int(booking.get("version", 1))},
        {"$set": {"status": "CANCELLED", "cancelled_at": utcnow(), "updated_at": utcnow()}, "$inc": {"version": 1}},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflict: stale booking version")

    meta = updated.get("meta") or {}
    refund_amount, _ = _rental_refund_amounts(meta, utcnow())
    if refund_amount > 0:
        await db.refunds.insert_one(
            {
                "id": f"ref_{uuid4().hex}",
                "booking_id": booking_id,
                "amount_paise": refund_amount,
                "status": "REQUESTED",
                "reason": payload.reason or "rental_cancelled",
                "created_at": utcnow(),
                "updated_at": utcnow(),
            }
        )

    lock_id = (updated.get("resource_lock_ids") or [None])[0]
    if lock_id:
        await release_lock(db, str(lock_id))

    return ResponseEnvelope[dict](
        success=True,
        data={"booking": updated, "refund_amount_paise": refund_amount},
        message="Rental booking cancelled",
        request_id=_request_id(request),
    )
