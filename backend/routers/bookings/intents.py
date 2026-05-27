"""Booking intent creation and payment order routes."""
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status

from canonical_models.booking import BookingIntentCreate
from canonical_models.common import BookingIntentStatus, ResponseEnvelope, utcnow
from core.database import get_db_from_request

from .helpers import (
    BookingPayResponse, _audit_log, _compute_booking_intent_items_and_total_from_db,
    _enforce_booking_creator_role, _enforce_total_tamper_threshold, _normalize_role,
    _payment_client_from_app, _request_id, _to_paise, get_current_user, limiter, logger, settings,
)

router = APIRouter()


@router.post("/intent", response_model=ResponseEnvelope[dict])
@limiter.limit("50/hour")
async def create_booking_intent(
    request: Request,
    payload: BookingIntentCreate = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    _enforce_booking_creator_role(current_user)
    db = get_db_from_request(request)

    vendor = await db.vendors.find_one({"id": payload.vendor_id})
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    if vendor.get("status") not in ["approved", "APPROVED"]:
        raise HTTPException(status_code=400, detail="Vendor is not currently accepting bookings")
    if vendor.get("is_active") == False:
        raise HTTPException(status_code=400, detail="Vendor account is inactive")
    if str(vendor.get("user_id") or "") == str(current_user.get("id") or ""):
        raise HTTPException(status_code=400, detail="You cannot book your own vendor profile")

    now = utcnow()
    expires_at = now + timedelta(minutes=30)

    server_items, server_total_amount_paise = await _compute_booking_intent_items_and_total_from_db(
        db,
        vendor_id=str(payload.vendor_id),
        raw_items=list(payload.items),
    )
    _enforce_total_tamper_threshold(payload.total_amount_paise, server_total_amount_paise)

    existing = await db.booking_intents.find_one({"idempotency_key": payload.idempotency_key}, {"_id": 0})
    if existing:
        return ResponseEnvelope[dict](
            success=True,
            data=existing,
            message="Idempotent intent replay",
            request_id=_request_id(request),
        )

    intent_doc = {
        "id": f"bint_{uuid4().hex}",
        "idempotency_key": payload.idempotency_key,
        "user_id": str(current_user.get("id")),
        "vendor_id": str(payload.vendor_id),
        "category_type": payload.category_type.value if hasattr(payload.category_type, "value") else str(payload.category_type),
        "items": server_items,
        "total_amount_paise": server_total_amount_paise,
        "scheduled_at": payload.scheduled_at,
        "duration_minutes": payload.duration_minutes,
        "notes": payload.notes,
        "meta": payload.meta or {},
        "status": BookingIntentStatus.PENDING.value,
        "expires_at": expires_at,
        "created_at": now,
        "updated_at": now,
        "version": 1,
    }

    await db.booking_intents.insert_one(intent_doc)
    await _audit_log(
        db=db,
        actor_id=str(current_user.get("id")),
        actor_role=_normalize_role(current_user.get("role")),
        action="booking_intent_created",
        entity_id=intent_doc["id"],
        request_id=_request_id(request),
        payload={"category_type": intent_doc.get("category_type"), "total_amount_paise": intent_doc.get("total_amount_paise")},
    )

    intent_doc.pop("_id", None)
    return ResponseEnvelope[dict](
        success=True,
        data=intent_doc,
        message="Booking intent created",
        request_id=_request_id(request),
    )


@router.post("/quote/{quote_id}/intent", response_model=ResponseEnvelope[dict])
@limiter.limit("50/hour")
async def create_booking_intent_from_quote(
    quote_id: str,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    _enforce_booking_creator_role(current_user)
    db = get_db_from_request(request)

    quote = await db.quotes.find_one({"id": quote_id})
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")
    if str(quote.get("user_id")) != str(current_user.get("id")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to accept this quote")
    status_str = str(quote.get("status") or "").lower()
    if status_str != "responded":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Quote status must be 'responded' to book, current status: {status_str}")

    vendor_id = str(quote["vendor_id"])
    vendor = await db.vendors.find_one({"id": vendor_id})
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    if vendor.get("status") not in ["approved", "APPROVED"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vendor is not currently accepting bookings")
    if vendor.get("is_active") == False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vendor account is inactive")

    quoted_price = quote.get("quoted_price")
    if quoted_price is None or float(quoted_price) <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Quote does not have a valid quoted price")
    quoted_price_paise = _to_paise(quoted_price)

    event_id = quote.get("event_id")
    event_date_str = None
    if event_id:
        event = await db.events.find_one({"id": event_id})
        if event:
            event_date_str = event.get("date")

    scheduled_at = None
    if event_date_str:
        try:
            scheduled_at = datetime.fromisoformat(f"{event_date_str}T12:00:00+05:30").astimezone(tz=utcnow().tzinfo)
        except Exception:
            try:
                scheduled_at = datetime.strptime(event_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except Exception:
                pass

    now_time = utcnow()
    expires_at = now_time + timedelta(minutes=30)
    idempotency_key = f"quote_intent_{quote_id}"

    existing = await db.booking_intents.find_one({"idempotency_key": idempotency_key}, {"_id": 0})
    if existing:
        return ResponseEnvelope[dict](
            success=True,
            data=existing,
            message="Idempotent intent replay",
            request_id=_request_id(request),
        )

    intent_doc = {
        "id": f"bint_{uuid4().hex}",
        "idempotency_key": idempotency_key,
        "user_id": str(current_user.get("id")),
        "vendor_id": vendor_id,
        "category_type": "service",
        "items": [
            {
                "item_id": f"quote_{quote_id}",
                "title": f"Custom Quoted Service ({quote_id})",
                "qty": 1,
                "unit_price_paise": quoted_price_paise,
                "total_price_paise": quoted_price_paise,
                "meta": {"quote_id": quote_id},
            }
        ],
        "total_amount_paise": quoted_price_paise,
        "scheduled_at": scheduled_at,
        "duration_minutes": 360,
        "notes": quote.get("response_message") or quote.get("message"),
        "meta": {"quote_id": quote_id, "event_id": event_id},
        "status": BookingIntentStatus.PENDING.value,
        "expires_at": expires_at,
        "created_at": now_time,
        "updated_at": now_time,
        "version": 1,
    }

    await db.booking_intents.insert_one(intent_doc)
    await db.quotes.update_one(
        {"id": quote_id},
        {"$set": {"status": "accepted", "responded_at": now_time}}
    )

    try:
        from workers.job_queue import enqueue_job
        await enqueue_job("send_quote_accepted_notification", quote_id)
        await enqueue_job("update_vendor_response_metrics", vendor_id)
    except Exception as queue_err:
        logger.error(f"Failed to enqueue quote accepted background jobs: {queue_err}")

    await _audit_log(
        db=db,
        actor_id=str(current_user.get("id")),
        actor_role=_normalize_role(current_user.get("role")),
        action="booking_intent_created_from_quote",
        entity_id=intent_doc["id"],
        request_id=_request_id(request),
        payload={"quote_id": quote_id, "total_amount_paise": quoted_price_paise},
    )

    return ResponseEnvelope[dict](
        success=True,
        data=intent_doc,
        message="Booking intent created from quote successfully",
        request_id=_request_id(request),
    )


@limiter.limit("20/hour")
@router.post("/{intent_id}/pay", response_model=ResponseEnvelope[BookingPayResponse])
async def create_payment_order_for_intent(
    intent_id: str,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    intent = await db.booking_intents.find_one({"id": intent_id}, {"_id": 0})
    if not intent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking intent not found")
    if str(intent.get("user_id")) != str(current_user.get("id")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this intent")
    if intent.get("status") != BookingIntentStatus.PENDING.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Intent is not payable")
    expires_at = intent.get("expires_at")
    if expires_at:
        now = utcnow()
        if expires_at.tzinfo is None and now.tzinfo is not None:
            now = now.replace(tzinfo=None)
        elif expires_at.tzinfo is not None and now.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=None)
        if expires_at <= now:
            await db.booking_intents.update_one(
                {"id": intent_id, "status": BookingIntentStatus.PENDING.value},
                {"$set": {"status": BookingIntentStatus.EXPIRED.value, "updated_at": utcnow()}, "$inc": {"version": 1}},
            )
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Intent expired")

    existing_payment = await db.payments.find_one(
        {"booking_intent_id": intent_id, "status": {"$in": ["CREATED", "CLIENT_VERIFIED", "CONFIRMED"]}},
        {"_id": 0, "razorpay_order_id": 1, "amount": 1, "currency": 1},
    )
    if existing_payment:
        data = BookingPayResponse(
            booking_intent_id=intent_id,
            razorpay_order_id=existing_payment["razorpay_order_id"],
            amount_paise=int(existing_payment.get("amount", 0)),
            currency=existing_payment.get("currency", "INR"),
            key_id=settings.RAZORPAY_KEY_ID,
        )
        return ResponseEnvelope[BookingPayResponse](
            success=True,
            data=data,
            message="Existing payment order reused",
            request_id=_request_id(request),
        )

    amount_paise = int(intent.get("total_amount_paise", 0) or 0)
    if amount_paise <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid intent amount")

    razorpay_client = _payment_client_from_app(request)
    razorpay_order = razorpay_client.order.create(
        {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": intent_id,
            "notes": {
                "booking_intent_id": intent_id,
                "user_id": str(current_user.get("id")),
            },
        }
    )

    payment_doc = {
        "id": f"pay_{uuid4().hex}",
        "booking_intent_id": intent_id,
        "booking_id": None,
        "amount": amount_paise,
        "currency": "INR",
        "status": "CREATED",
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_payment_id": None,
        "razorpay_signature": None,
        "idempotency_key": f"{intent_id}:{razorpay_order['id']}",
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    await db.payments.insert_one(payment_doc)
    await _audit_log(
        db=db,
        actor_id=str(current_user.get("id")),
        actor_role=_normalize_role(current_user.get("role")),
        action="booking_payment_order_created",
        entity_id=intent_id,
        request_id=_request_id(request),
        payload={"razorpay_order_id": razorpay_order["id"], "amount_paise": amount_paise},
    )

    return ResponseEnvelope[BookingPayResponse](
        success=True,
        data=BookingPayResponse(
            booking_intent_id=intent_id,
            razorpay_order_id=razorpay_order["id"],
            amount_paise=amount_paise,
            currency="INR",
            key_id=settings.RAZORPAY_KEY_ID,
        ),
        message="Payment order created",
        request_id=_request_id(request),
    )
