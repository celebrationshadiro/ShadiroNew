from __future__ import annotations

import hashlib
import hmac
import json
import logging
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument, errors

from core.config import get_settings
from core.database import get_db_from_request
from core.prometheus import observe_payment_latency
from core.security import get_current_user, get_rate_limiter
from canonical_models.common import BookingIntentStatus, BookingStatus, ResponseEnvelope, utcnow
from integrations.grocery_delivery_bridge import try_spawn_grocery_delivery_after_paid_booking
from payments.execution_service import PaymentExecutionService

router = APIRouter(prefix="/api/bookings", tags=["payments"])
settings = get_settings()
logger = logging.getLogger(__name__)
limiter = get_rate_limiter()

# In-process webhook rate limiter: max 100 requests/minute per IP.
_WEBHOOK_RATE_LIMIT = 100
_WEBHOOK_RATE_WINDOW_SECONDS = 60
_webhook_rate_buckets: dict[str, deque[float]] = defaultdict(deque)
_webhook_rate_lock = threading.Lock()


class ClientVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    razorpay_order_id: str = Field(min_length=8)
    razorpay_payment_id: str = Field(min_length=8)
    razorpay_signature: str = Field(min_length=8)
    idempotency_key: str = Field(min_length=8, max_length=128)
    booking_intent_id: Optional[str] = None


class RazorpayWebhookPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    event: str
    payload: dict[str, Any]
    created_at: Optional[int] = None


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


def _payment_client_from_app(request: Request):
    client = getattr(request.app.state, "razorpay_client", None)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment provider unavailable",
        )
    return client


def _webhook_secret() -> str:
    secret = (
        getattr(settings, "RAZORPAY_WEBHOOK_SECRET", None)
        or getattr(settings, "RAZORPAY_WEBHOOK_KEY", None)
        or ""
    )
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret not configured",
        )
    return secret


def _verify_webhook_signature(event_id: str, raw_body: bytes, signature: str) -> bool:
    if not event_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing event ID in webhook payload")
    msg = f"{event_id}{raw_body.decode('utf-8')}".encode("utf-8")
    expected = hmac.new(
        _webhook_secret().encode("utf-8"),
        msg,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _signature_preview(signature: str | None) -> str:
    if not signature:
        return "<missing>"
    s = str(signature)
    return f"{s[:8]}...({len(s)})"


async def get_raw_body(request: Request) -> bytes:
    # Must read exact raw body bytes for Razorpay webhook HMAC verification.
    return await request.body()


async def enforce_webhook_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now_ts = time.time()
    with _webhook_rate_lock:
        bucket = _webhook_rate_buckets[ip]
        cutoff = now_ts - _WEBHOOK_RATE_WINDOW_SECONDS
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= _WEBHOOK_RATE_LIMIT:
            logger.warning(
                "webhook_rate_limited ip=%s ts=%s event=%s sig_prefix=%s",
                ip,
                utcnow().isoformat(),
                "unknown",
                "<n/a>",
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded for webhook",
            )
        bucket.append(now_ts)


async def verify_razorpay_signature(
    request: Request,
    raw_body: bytes = Depends(get_raw_body),
    x_razorpay_signature: str | None = Header(default=None, alias="x-razorpay-signature"),
) -> str:
    ip = request.client.host if request.client else "unknown"
    timestamp = utcnow().isoformat()
    event_type = "unknown"
    event_id = ""
    try:
        body_dict = json.loads(raw_body.decode("utf-8"))
        event_type = str(body_dict.get("event") or "unknown")
        event_id = str(body_dict.get("id", "")).strip()
    except Exception:
        event_type = "unknown"
        event_id = ""

    if not x_razorpay_signature:
        logger.warning(
            "webhook_signature_missing ip=%s ts=%s event=%s sig_prefix=%s",
            ip,
            timestamp,
            event_type,
            "<missing>",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing webhook signature")

    if not event_id:
        logger.warning(
            "webhook_event_id_missing ip=%s ts=%s event=%s sig_prefix=%s",
            ip,
            timestamp,
            event_type,
            _signature_preview(x_razorpay_signature),
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing event ID in webhook payload")

    if not _verify_webhook_signature(event_id, raw_body, x_razorpay_signature):
        logger.warning(
            "webhook_signature_invalid ip=%s ts=%s event=%s sig_prefix=%s",
            ip,
            timestamp,
            event_type,
            str(x_razorpay_signature)[:10],
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")
    return x_razorpay_signature


async def _audit_log(
    *,
    db,
    actor_id: str,
    actor_role: str,
    action: str,
    entity_id: Optional[str],
    request_id: str,
    payload: dict[str, Any] | None = None,
) -> None:
    await db.audit_logs.insert_one(
        {
            "id": f"audit_{uuid4().hex}",
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action": action,
            "entity_type": "payment",
            "entity_id": entity_id,
            "payload": payload or {},
            "request_id": request_id,
            "created_at": utcnow(),
        }
    )


async def _resolve_payment_and_intent(
    *,
    db,
    razorpay_order_id: str,
    requested_intent_id: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    payment = await db.payments.find_one({"razorpay_order_id": razorpay_order_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment order not found")

    intent_id = requested_intent_id or payment.get("booking_intent_id")
    if not intent_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment has no booking intent mapping")

    intent = await db.booking_intents.find_one({"id": intent_id}, {"_id": 0})
    if not intent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking intent not found")
    return payment, intent


async def _compute_financials(db, intent: dict[str, Any]) -> dict[str, int]:
    gross = int(intent.get("total_amount_paise", 0) or 0)
    if gross <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid intent amount")

    vendor = await db.vendors.find_one(
        {"id": intent["vendor_id"]},
        {"_id": 0, "commission_override_bps": 1, "category_id": 1},
    )
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")

    override_bps = vendor.get("commission_override_bps")
    if isinstance(override_bps, int) and 0 <= override_bps <= 10000:
        rate_bps = override_bps
    else:
        rate_bps = 1000
        category_id = vendor.get("category_id")
        if category_id:
            category = await db.vendor_categories.find_one(
                {"id": category_id},
                {"_id": 0, "default_commission_bps": 1},
            )
            category_rate = (category or {}).get("default_commission_bps")
            if isinstance(category_rate, int) and 0 <= category_rate <= 10000:
                rate_bps = category_rate
            else:
                config = await db.platform_config.find_one(
                    {"key": "commission_defaults"},
                    {"_id": 0, "default_commission_bps": 1},
                )
                cfg_rate = (config or {}).get("default_commission_bps")
                if isinstance(cfg_rate, int) and 0 <= cfg_rate <= 10000:
                    rate_bps = cfg_rate

    commission = (gross * rate_bps) // 10000
    vendor_net = gross - commission
    return {
        "gross": gross,
        "commission_rate_bps": rate_bps,
        "commission_amount_paise": commission,
        "vendor_net_paise": vendor_net,
    }


async def _materialize_booking_from_intent(
    *,
    db,
    intent: dict[str, Any],
    payment: dict[str, Any],
    source: str,
) -> dict[str, Any]:
    existing = await db.bookings.find_one({"intent_id": intent["id"]}, {"_id": 0})
    if existing:
        await db.payments.update_one(
            {"id": payment["id"]},
            {"$set": {"booking_id": existing["id"], "updated_at": utcnow()}},
        )
        return existing

    financials = await _compute_financials(db, intent)
    now = utcnow()
    booking_doc = {
        "id": f"book_{uuid4().hex}",
        "intent_id": intent["id"],
        "user_id": intent["user_id"],
        "vendor_id": intent["vendor_id"],
        "category_type": intent["category_type"],
        "items": intent.get("items", []),
        "status": BookingStatus.PAYMENT_RECEIVED.value,
        "version": 1,
        "scheduled_at": intent.get("scheduled_at"),
        "duration_minutes": intent.get("duration_minutes"),
        "amount_gross_paise": financials["gross"],
        "commission_rate_bps": financials["commission_rate_bps"],
        "commission_amount_paise": financials["commission_amount_paise"],
        "vendor_net_paise": financials["vendor_net_paise"],
        "payment_id": payment["id"],
        "resource_lock_ids": [],
        "notes": intent.get("notes"),
        "meta": {
            **(intent.get("meta") or {}),
            "payment_source": source,
            "escrow_state": "HELD" if str(intent.get("category_type")).lower() == "service" else "N/A",
        },
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
        "cancelled_at": None,
    }

    await db.bookings.insert_one(booking_doc)
    await db.booking_intents.update_one(
        {"id": intent["id"], "status": BookingIntentStatus.PENDING.value},
        {
            "$set": {"status": BookingIntentStatus.CONVERTED.value, "updated_at": now},
            "$inc": {"version": 1},
        },
    )
    await db.payments.update_one(
        {"id": payment["id"]},
        {"$set": {"booking_id": booking_doc["id"], "updated_at": now}},
    )
    await db.state_transitions.insert_one(
        {
            "id": f"st_{uuid4().hex}",
            "entity_type": "BOOKING",
            "entity_id": booking_doc["id"],
            "from_status": BookingStatus.AWAITING_PAYMENT.value,
            "to_status": BookingStatus.PAYMENT_RECEIVED.value,
            "actor_role": "system",
            "actor_id": "system",
            "reason": f"Payment confirmed via {source}",
            "created_at": now,
        }
    )
    return booking_doc


async def _apply_rental_payment_update(
    *,
    db,
    booking: dict[str, Any],
    payment: dict[str, Any],
) -> None:
    if str(booking.get("category_type")).lower() != "rental":
        return

    meta = booking.get("meta") or {}
    deposit_paise = int(meta.get("deposit_amount_paise", 0) or 0)
    balance_paise = int(meta.get("balance_amount_paise", 0) or 0)
    payment_amount = int(payment.get("amount", 0) or 0)
    now = utcnow()

    updates: dict[str, Any] = {}
    if deposit_paise and payment_amount == deposit_paise and not meta.get("deposit_paid_at"):
        updates.update(
            {
                "meta.deposit_paid_at": now,
                "meta.deposit_payment_id": payment.get("id"),
                "meta.deposit_paid": True,
            }
        )
    if balance_paise and payment_amount == balance_paise and not meta.get("balance_paid_at"):
        updates.update(
            {
                "meta.balance_paid_at": now,
                "meta.balance_payment_id": payment.get("id"),
                "meta.balance_paid": True,
            }
        )

    if updates:
        updates["updated_at"] = now
        await db.bookings.update_one(
            {"id": booking["id"]},
            {"$set": updates, "$inc": {"version": 1}},
        )


@limiter.limit("30/hour")
@router.post("/verify", response_model=ResponseEnvelope[dict])
async def verify_payment_client(
    request: Request,
    payload: ClientVerifyRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    started_at = time.perf_counter()
    db = get_db_from_request(request)

    # Idempotency check: if this idempotency_key was already processed, return cached result
    existing_payment = await db.payments.find_one(
        {"idempotency_key": payload.idempotency_key},
        {"_id": 0}
    )
    if existing_payment:
        existing_booking = await db.bookings.find_one(
            {"payment_id": existing_payment.get("id")},
            {"_id": 0}
        )
        if existing_booking:
            return ResponseEnvelope[dict](
                success=True,
                data={
                    "payment_status": existing_payment.get("status"),
                    "booking_id": existing_booking.get("id"),
                    "booking_status": existing_booking.get("status"),
                    "already_processed": True,
                },
                message="Payment already processed",
                request_id=_request_id(request),
            )

    payment, intent = await _resolve_payment_and_intent(
        db=db,
        razorpay_order_id=payload.razorpay_order_id,
        requested_intent_id=payload.booking_intent_id,
    )
    if str(intent.get("user_id")) != str(current_user.get("id")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this payment")

    if payment.get("status") in {"CLIENT_VERIFIED", "CONFIRMED"}:
        booking = await _materialize_booking_from_intent(
            db=db,
            intent=intent,
            payment=payment,
            source="client_verify",
        )
        await try_spawn_grocery_delivery_after_paid_booking(
            db=db,
            app_state=request.app.state,
            booking=booking,
            intent=intent,
            settings=get_settings(),
        )
        return ResponseEnvelope[dict](
            success=True,
            data={
                "payment_status": payment.get("status"),
                "booking_id": booking["id"],
                "booking_status": booking["status"],
                "idempotent_replay": True,
            },
            message="Payment already verified",
            request_id=_request_id(request),
        )

    client = _payment_client_from_app(request)
    try:
        await run_in_threadpool(
            client.utility.verify_payment_signature,
            {
                "razorpay_order_id": payload.razorpay_order_id,
                "razorpay_payment_id": payload.razorpay_payment_id,
                "razorpay_signature": payload.razorpay_signature,
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment signature verification failed") from exc

    now = utcnow()
    updated_payment = await db.payments.find_one_and_update(
        {
            "id": payment["id"],
            "status": {"$in": ["CREATED", "CLIENT_VERIFIED"]},
        },
        {
            "$set": {
                "status": "CLIENT_VERIFIED",
                "razorpay_payment_id": payload.razorpay_payment_id,
                "razorpay_signature": payload.razorpay_signature,
                "idempotency_key": payload.idempotency_key,
                "updated_at": now,
            }
        },
        return_document=ReturnDocument.AFTER,
        projection={"_id": 0},
    )
    if not updated_payment:
        payment = await db.payments.find_one({"id": payment["id"]}, {"_id": 0})
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        updated_payment = payment

    booking = await _materialize_booking_from_intent(
        db=db,
        intent=intent,
        payment=updated_payment,
        source="client_verify",
    )
    await try_spawn_grocery_delivery_after_paid_booking(
        db=db,
        app_state=request.app.state,
        booking=booking,
        intent=intent,
        settings=get_settings(),
    )
    await _apply_rental_payment_update(db=db, booking=booking, payment=updated_payment)

    await _audit_log(
        db=db,
        actor_id=str(current_user.get("id")),
        actor_role=str(current_user.get("role", "customer")).lower(),
        action="payment_client_verified",
        entity_id=updated_payment["id"],
        request_id=_request_id(request),
        payload={"booking_id": booking["id"], "razorpay_order_id": payload.razorpay_order_id},
    )

    response = ResponseEnvelope[dict](
        success=True,
        data={
            "payment_status": updated_payment["status"],
            "booking_id": booking["id"],
            "booking_status": booking["status"],
            "idempotent_replay": False,
        },
        message="Payment verification accepted",
        request_id=_request_id(request),
    )
    observe_payment_latency("client_verify", time.perf_counter() - started_at)
    return response


@router.get("/{booking_id}/payment/status", response_model=ResponseEnvelope[dict])
async def get_booking_payment_status(
    booking_id: str,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if str(booking.get("user_id")) != str(current_user.get("id")) and str(current_user.get("role", "")).lower() != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this booking")

    payment = None
    if booking.get("payment_id"):
        payment = await db.payments.find_one({"id": booking["payment_id"]}, {"_id": 0})
    if payment is None:
        payment = await db.payments.find_one({"booking_id": booking_id}, {"_id": 0})

    return ResponseEnvelope[dict](
        success=True,
        data={
            "booking_id": booking_id,
            "status": (payment or {}).get("status", "NOT_FOUND"),
        },
        message="Payment status fetched",
        request_id=_request_id(request),
    )


@router.post(
    "/webhook",
    response_model=ResponseEnvelope[dict],
    openapi_extra={
        "parameters": [
            {
                "name": "x-razorpay-signature",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
            },
            {
                "name": "x-razorpay-event-id",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
            },
        ],
        "security": [],
    },
)
async def razorpay_webhook(
    request: Request,
    payload: RazorpayWebhookPayload,
    raw_body: bytes = Depends(get_raw_body),
    _: None = Depends(enforce_webhook_rate_limit),
    verified_signature: str = Depends(verify_razorpay_signature),
    x_razorpay_event_id: str | None = Header(default=None, alias="x-razorpay-event-id"),
):
    db = get_db_from_request(request)
    event_id = str(x_razorpay_event_id or "").strip()
    if not event_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing x-razorpay-event-id header")
    
    # Only process payment.captured events
    ALLOWED_EVENTS = frozenset({"payment.captured"})
    event_type = payload.event
    if event_type not in ALLOWED_EVENTS:
        return ResponseEnvelope[dict](
            success=True,
            data={"processed": False, "reason": "event_not_actionable"},
            message="Event not actionable",
            request_id=_request_id(request),
        )
    
    # Verify amount matches stored record
    payment_entity = payload.payload.get("payment", {}).get("entity", {})
    order_id = payment_entity.get("order_id")
    received_amount = payment_entity.get("amount")
    received_currency = payment_entity.get("currency")
    
    if not order_id:
        raise HTTPException(status_code=400, detail="Missing order_id in webhook")
    
    stored_payment = await db.payments.find_one({"razorpay_order_id": order_id})
    if not stored_payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    stored_amount = stored_payment.get("amount") or stored_payment.get("amount_paise")
    if received_amount != stored_amount:
        raise HTTPException(status_code=400, detail="Amount mismatch — possible fraud")
    if received_currency != "INR":
        raise HTTPException(status_code=400, detail="Invalid currency")
    
    # Reject webhooks older than 5 minutes (replay protection)
    webhook_ts = payload.created_at or int(time.time())
    if abs(int(time.time()) - webhook_ts) > 300:
        raise HTTPException(status_code=400, detail="Webhook too old — replay attack suspected")
    
    # Deduplicate by event_id
    try:
        await db.webhook_events.insert_one({"event_id": event_id, "received_at": utcnow()})
    except errors.DuplicateKeyError:
        return ResponseEnvelope[dict](
            success=True,
            data={"processed": False, "reason": "duplicate_event"},
            message="Duplicate event",
            request_id=_request_id(request),
        )
    except Exception as e:
        raise
    
    service = PaymentExecutionService(db=db, razorpay_client=_payment_client_from_app(request))
    result = await service.process_payment_captured_webhook(
        event_id=event_id,
        event=event_type,
        payload=payload.model_dump(mode="python"),
        signature=verified_signature,
        request_id=_request_id(request),
        app_state=request.app.state,
    )

    return ResponseEnvelope[dict](
        success=True,
        data=result,
        message="Webhook processed",
        request_id=_request_id(request),
    )
