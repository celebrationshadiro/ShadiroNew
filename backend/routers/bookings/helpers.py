"""Shared DTOs, constants, and helper functions for the bookings package."""
from datetime import date, datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

from fastapi import HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument

from booking_engine.category_config import SERVICE_CATEGORIES, normalize_category_slug
from booking_engine.lock_service import acquire_slot_lock, acquire_date_range_lock, release_lock, utcnow as be_utcnow
from core.config import get_settings
from core.database import get_db_from_request
from core.security import enforce_owner_or_admin, enforce_vendor_or_admin, get_current_user, require_admin, get_rate_limiter
from core.settlement import SettlementService
from canonical_models.booking import BookingActionRequest, BookingIntentCreate
from canonical_models.common import BookingAction, BookingIntentStatus, BookingStatus, ResponseEnvelope, UserRole, utcnow
from payments.execution_service import PaymentExecutionService
from services.pricing_engine import apply_pricing_rules

import logging
logger = logging.getLogger(__name__)

settings = get_settings()
limiter = get_rate_limiter()


# ── Request/Response DTOs ────────────────────────────────────────────────────

class BookingPayResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    booking_intent_id: str
    razorpay_order_id: str
    amount_paise: int
    currency: str = "INR"
    key_id: str


class ServiceIntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vendor_id: str
    package_id: str
    category_slug: str
    event_date: str
    event_time: str
    guest_count: int = Field(default=1, ge=1)
    notes: Optional[str] = None
    idempotency_key: str = Field(min_length=8, max_length=128)
    category_meta: dict[str, Any] = {}


class RentalAvailabilityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    available: bool
    conflicting_dates: list[str] = []


class RentalIntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vendor_id: str
    item_id: str
    category_slug: str
    check_in_date: str
    check_out_date: str
    notes: Optional[str] = None
    idempotency_key: str = Field(min_length=8, max_length=128)
    category_meta: dict[str, Any] = {}


class RentalPayBalanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: Optional[str] = None


class RentalCancelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(min_length=3, max_length=500)


class BookingOrderLinkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_id: str = Field(min_length=3)


class BookingCancelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(min_length=3, max_length=500)
    expected_version: int = Field(ge=1)


class BookingListItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    intent_id: Optional[str] = None
    user_id: Optional[str] = None
    vendor_id: Optional[str] = None
    category_type: Optional[str] = None
    status: str
    version: int = 1
    amount_gross_paise: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BookingDetail(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    intent_id: Optional[str] = None
    user_id: Optional[str] = None
    vendor_id: Optional[str] = None
    category_type: Optional[str] = None
    items: list[dict[str, Any]] = []
    status: str
    version: int = 1
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    amount_gross_paise: int = 0
    commission_rate_bps: int = 0
    commission_amount_paise: int = 0
    vendor_net_paise: int = 0
    payment_id: Optional[str] = None
    resource_lock_ids: list[str] = []
    notes: Optional[str] = None
    meta: dict[str, Any] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None


class BookingOrderBridgeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    booking_id: str
    order_id: Optional[str] = None


class BookingTransitionItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    entity_type: str
    entity_id: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    actor_role: Optional[str] = None
    actor_id: Optional[str] = None
    reason: Optional[str] = None
    created_at: Optional[datetime] = None


# ── Constants ────────────────────────────────────────────────────────────────

SERVICE_CATEGORY_META_FIELDS: dict[str, set[str]] = {
    "photography": {"shoot_type", "hours_required"},
    "catering": {"menu_type", "meals_count", "cuisine_type"},
    "decoration": {"theme", "venue_size_sqft", "decoration_type"},
    "makeup": {"service_type", "artists_count"},
    "lighting": {"lighting_type", "setup_hours", "equipment_list"},
    "videography": {"video_type", "hours_required", "drone_required"},
}

ROLE_ALLOWED_ACTIONS: dict[str, set[str]] = {
    UserRole.CUSTOMER.value: {"cancel", "confirm_completion"},
    UserRole.VENDOR.value: {"accept", "reject", "mark_progress", "complete", "cancel"},
    UserRole.ADMIN.value: {"accept", "reject", "complete", "cancel", "force_refund"},
}

BOOKING_TRANSITIONS: dict[tuple[str, str, str], str] = {
    # Canonical bookings
    ("PAYMENT_RECEIVED", "accept", UserRole.VENDOR.value): "CONFIRMED",
    ("PAYMENT_RECEIVED", "reject", UserRole.VENDOR.value): "CANCELLED",
    ("CONFIRMED", "mark_progress", UserRole.VENDOR.value): "IN_PROGRESS",
    ("CONFIRMED", "complete", UserRole.VENDOR.value): "COMPLETED",
    ("IN_PROGRESS", "complete", UserRole.VENDOR.value): "COMPLETED",
    ("PAYMENT_RECEIVED", "cancel", UserRole.CUSTOMER.value): "CANCELLED",
    ("CONFIRMED", "cancel", UserRole.CUSTOMER.value): "CANCELLED",
    ("IN_PROGRESS", "cancel", UserRole.CUSTOMER.value): "CANCELLED",
    ("IN_PROGRESS", "confirm_completion", UserRole.CUSTOMER.value): "COMPLETED",
    ("CONFIRMED", "confirm_completion", UserRole.CUSTOMER.value): "COMPLETED",
    ("PAYMENT_RECEIVED", "accept", UserRole.ADMIN.value): "CONFIRMED",
    ("PAYMENT_RECEIVED", "reject", UserRole.ADMIN.value): "CANCELLED",
    ("CONFIRMED", "complete", UserRole.ADMIN.value): "COMPLETED",
    ("IN_PROGRESS", "complete", UserRole.ADMIN.value): "COMPLETED",
    ("PAYMENT_RECEIVED", "cancel", UserRole.ADMIN.value): "CANCELLED",
    ("CONFIRMED", "cancel", UserRole.ADMIN.value): "CANCELLED",
    ("IN_PROGRESS", "cancel", UserRole.ADMIN.value): "CANCELLED",
    ("COMPLETED", "force_refund", UserRole.ADMIN.value): "REFUNDED",
    ("CANCELLED", "force_refund", UserRole.ADMIN.value): "REFUNDED",
    ("PAYMENT_RECEIVED", "force_refund", UserRole.ADMIN.value): "REFUNDED",
    ("CONFIRMED", "force_refund", UserRole.ADMIN.value): "REFUNDED",
    ("IN_PROGRESS", "force_refund", UserRole.ADMIN.value): "REFUNDED",
    # Service bookings (legacy collection)
    ("PENDING_VENDOR", "accept", UserRole.VENDOR.value): "CONFIRMED",
    ("PENDING_VENDOR", "reject", UserRole.VENDOR.value): "REFUNDED",
    ("PENDING_VENDOR", "cancel", UserRole.CUSTOMER.value): "CANCELLED",
    ("CONFIRMED", "mark_progress", UserRole.VENDOR.value): "IN_PROGRESS",
    ("CONFIRMED", "complete", UserRole.VENDOR.value): "COMPLETED",
    ("IN_PROGRESS", "complete", UserRole.VENDOR.value): "COMPLETED",
    ("CONFIRMED", "cancel", UserRole.CUSTOMER.value): "CANCELLED",
    ("IN_PROGRESS", "cancel", UserRole.CUSTOMER.value): "CANCELLED",
    ("IN_PROGRESS", "confirm_completion", UserRole.CUSTOMER.value): "COMPLETED",
    ("CONFIRMED", "confirm_completion", UserRole.CUSTOMER.value): "COMPLETED",
    ("PENDING_VENDOR", "accept", UserRole.ADMIN.value): "CONFIRMED",
    ("PENDING_VENDOR", "reject", UserRole.ADMIN.value): "REFUNDED",
    ("CONFIRMED", "complete", UserRole.ADMIN.value): "COMPLETED",
    ("IN_PROGRESS", "complete", UserRole.ADMIN.value): "COMPLETED",
    ("PENDING_VENDOR", "cancel", UserRole.ADMIN.value): "CANCELLED",
    ("CONFIRMED", "cancel", UserRole.ADMIN.value): "CANCELLED",
    ("IN_PROGRESS", "cancel", UserRole.ADMIN.value): "CANCELLED",
    ("CONFIRMED", "force_refund", UserRole.ADMIN.value): "REFUNDED",
    ("IN_PROGRESS", "force_refund", UserRole.ADMIN.value): "REFUNDED",
    ("PENDING_VENDOR", "force_refund", UserRole.ADMIN.value): "REFUNDED",
    ("COMPLETED", "force_refund", UserRole.ADMIN.value): "REFUNDED",
}


# ── Helper functions ─────────────────────────────────────────────────────────

def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


def _to_booking_list_item(doc: dict[str, Any]) -> BookingListItem:
    return BookingListItem(
        id=str(doc.get("id") or ""),
        intent_id=doc.get("intent_id"),
        user_id=doc.get("user_id"),
        vendor_id=doc.get("vendor_id"),
        category_type=doc.get("category_type"),
        status=str(doc.get("status") or ""),
        version=int(doc.get("version", 1) or 1),
        amount_gross_paise=int(
            doc.get("amount_gross_paise")
            or doc.get("total_amount_paise")
            or doc.get("amount_paise")
            or 0
        ),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )


def _to_booking_detail(doc: dict[str, Any]) -> BookingDetail:
    return BookingDetail.model_validate(doc)


def _normalize_role(raw_role: str | None) -> str:
    role = str(raw_role or "").lower()
    if role == "user":
        return UserRole.CUSTOMER.value
    return role


def _enforce_booking_creator_role(current_user: dict[str, Any]) -> None:
    role = _normalize_role(current_user.get("role"))
    if role not in {UserRole.CUSTOMER.value, UserRole.ADMIN.value}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customer/admin accounts can create booking intents",
        )


async def _fetch_booking_any_or_404(db, booking_id: str) -> tuple[str, dict[str, Any]]:
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if booking:
        return "bookings", booking
    service_booking = await db.service_bookings.find_one({"id": booking_id}, {"_id": 0})
    if service_booking:
        return "service_bookings", service_booking
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")


def _booking_customer_id(booking: dict[str, Any]) -> str:
    return str(booking.get("user_id") or booking.get("customer_id") or "")


async def _enforce_booking_actor_access(db, booking: dict[str, Any], current_user: dict[str, Any]) -> None:
    role = _normalize_role(current_user.get("role"))
    if role == UserRole.ADMIN.value:
        return
    if role == UserRole.CUSTOMER.value:
        if _booking_customer_id(booking) != str(current_user.get("id")):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your booking")
        return
    if role == UserRole.VENDOR.value:
        vendor_doc = await db.vendors.find_one({"id": booking.get("vendor_id")}, {"_id": 0, "user_id": 1})
        enforce_vendor_or_admin(
            current_user=current_user,
            vendor_user_id=(vendor_doc or {}).get("user_id"),
            resource_name="booking",
        )
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid role for booking action")


def _resolve_next_status(*, current_status: str, action: str, role: str) -> str:
    next_status = BOOKING_TRANSITIONS.get((current_status, action, role))
    if not next_status:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Illegal transition for status={current_status}, action={action}, role={role}",
        )
    return next_status


def _allowed_actions_for_status(*, current_status: str, role: str) -> list[str]:
    role_actions = ROLE_ALLOWED_ACTIONS.get(role, set())
    allowed = [
        action
        for action in sorted(role_actions)
        if (current_status, action, role) in BOOKING_TRANSITIONS
    ]
    return allowed


async def _apply_action_side_effects(
    *,
    db,
    collection_name: str,
    before: dict[str, Any],
    after: dict[str, Any],
    action: str,
    reason: Optional[str],
) -> None:
    if collection_name == "service_bookings":
        lock_id = before.get("slot_lock_id")
        if lock_id and after.get("status") in {"CANCELLED", "REFUNDED"}:
            await release_lock(db, str(lock_id))
        if action in {"reject", "cancel", "force_refund"} and int(before.get("amount_paise", 0) or 0) > 0:
            await db.refunds.insert_one(
                {
                    "id": f"ref_{uuid4().hex}",
                    "booking_id": str(before.get("id")),
                    "amount_paise": int(before.get("amount_paise", 0) or 0),
                    "status": "REQUESTED",
                    "reason": reason or f"service_{action}",
                    "created_at": utcnow(),
                    "updated_at": utcnow(),
                }
            )
        return

    if collection_name == "bookings":
        lock_id = (before.get("resource_lock_ids") or [None])[0]
        if lock_id and after.get("status") in {"CANCELLED", "REFUNDED"}:
            await release_lock(db, str(lock_id))


async def handle_booking_action(
    *,
    request: Request,
    booking_id: str,
    payload: BookingActionRequest,
    current_user: dict[str, Any],
) -> dict[str, Any]:
    db = get_db_from_request(request)
    collection_name, booking = await _fetch_booking_any_or_404(db, booking_id)
    await _enforce_booking_actor_access(db, booking, current_user)

    role = _normalize_role(current_user.get("role"))
    action = payload.action.value if isinstance(payload.action, BookingAction) else str(payload.action)
    if action not in ROLE_ALLOWED_ACTIONS.get(role, set()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role-action permission denied")

    current_version = int(booking.get("version", 1))
    if current_version != int(payload.expected_version):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflict: stale booking version")

    current_status = str(booking.get("status") or "")
    next_status = _resolve_next_status(current_status=current_status, action=action, role=role)
    if next_status == "COMPLETED" and collection_name == "bookings":
        payout_service = PaymentExecutionService(
            db=db,
            razorpay_client=_payment_client_from_app(request),
        )
        payout_key = f"booking-complete:{booking_id}:{current_version}"
        await payout_service.execute_booking_payout(
            booking=booking,
            actor_id=str(current_user.get("id")),
            idempotency_key=payout_key,
            request_id=_request_id(request),
        )
    now = utcnow()
    update_set: dict[str, Any] = {"status": next_status, "updated_at": now}
    if next_status == "COMPLETED":
        update_set["completed_at"] = now
    if next_status in {"CANCELLED", "REFUNDED"}:
        update_set["cancelled_at"] = now
    if collection_name == "service_bookings":
        if action in {"accept", "reject"}:
            update_set["vendor_response_at"] = now
            update_set["rejection_reason"] = payload.reason if action == "reject" else None
        if action == "cancel":
            update_set["cancelled_at"] = now

    updated = await db[collection_name].find_one_and_update(
        {"id": booking_id, "version": current_version, "status": current_status},
        {"$set": update_set, "$inc": {"version": 1}},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflict: stale state or version")

    await db.state_transitions.insert_one(
        {
            "entity_type": "BOOKING",
            "entity_id": booking_id,
            "collection": collection_name,
            "from_status": current_status,
            "to_status": next_status,
            "actor_role": role,
            "actor_id": str(current_user.get("id")),
            "reason": payload.reason,
            "created_at": now,
        }
    )
    await _apply_action_side_effects(
        db=db,
        collection_name=collection_name,
        before=booking,
        after=updated,
        action=action,
        reason=payload.reason,
    )

    await _audit_log(
        db=db,
        actor_id=str(current_user.get("id")),
        actor_role=role,
        action=f"booking_action_{action}",
        entity_id=booking_id,
        request_id=_request_id(request),
        payload={
            "collection": collection_name,
            "from_status": current_status,
            "to_status": next_status,
            "expected_version": payload.expected_version,
            "new_version": updated.get("version"),
        },
    )
    return updated


def _payment_client_from_app(request: Request):
    client = getattr(request.app.state, "razorpay_client", None)
    if client is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Payment provider unavailable")
    return client


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
            "entity_type": "booking",
            "entity_id": entity_id,
            "payload": payload or {},
            "request_id": request_id,
            "created_at": utcnow(),
        }
    )


async def _fetch_booking_or_404(db, booking_id: str) -> dict[str, Any]:
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return booking


async def _resolve_vendor_id_for_user(db, current_user: dict[str, Any]) -> str:
    vendor = await db.vendors.find_one({"user_id": str(current_user.get("id"))}, {"_id": 0, "id": 1})
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor profile not found")
    return str(vendor["id"])


def _validate_service_category_meta(category_slug: str, category_meta: dict[str, Any]) -> None:
    required = SERVICE_CATEGORY_META_FIELDS.get(category_slug, set())
    missing = [k for k in sorted(required) if category_meta.get(k) in (None, "")]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing category_meta fields: {', '.join(missing)}",
        )


def _safe_event_datetime(event_date: str, event_time: str):
    try:
        return datetime.fromisoformat(f"{event_date}T{event_time}:00+05:30").astimezone(tz=utcnow().tzinfo)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid event_date or event_time") from exc


def _parse_date_string(value: str) -> str:
    raw = str(value or "").strip()
    if len(raw) != 10:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid date format")
    return raw


def _parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid date format") from exc


def _to_paise(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    try:
        return int(round(float(value) * 100))
    except Exception:
        return 0


async def _lookup_item_unit_price_paise(db, *, vendor_id: str, item_id: str) -> tuple[int, str]:
    grocery_item = await db.grocery_items.find_one(
        {"id": item_id, "vendor_id": vendor_id, "is_available": {"$ne": False}},
        {"_id": 0, "name": 1, "unit_price_paise": 1, "unit_price": 1},
    )
    if grocery_item:
        unit_price_paise = int(grocery_item.get("unit_price_paise") or _to_paise(grocery_item.get("unit_price")))
        if unit_price_paise <= 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid price for item {item_id}")
        return unit_price_paise, str(grocery_item.get("name") or item_id)

    definition = await db.service_definitions.find_one(
        {"vendor_id": vendor_id, "service_items.id": item_id},
        {"_id": 0, "service_items": {"$elemMatch": {"id": item_id}}},
    )
    if definition and definition.get("service_items"):
        service_item = definition["service_items"][0]
        unit_price_paise = int(service_item.get("unit_price_paise") or _to_paise(service_item.get("unit_price")))
        if unit_price_paise <= 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid price for item {item_id}")
        return unit_price_paise, str(service_item.get("name") or item_id)

    package = await db.packages.find_one(
        {"id": item_id, "vendor_id": vendor_id, "is_active": {"$ne": False}},
        {"_id": 0, "name": 1, "price": 1},
    )
    if package:
        unit_price_paise = _to_paise(package.get("price"))
        if unit_price_paise <= 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid price for item {item_id}")
        return unit_price_paise, str(package.get("name") or item_id)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item not found: {item_id}")


async def _compute_booking_intent_items_and_total_from_db(
    db,
    *,
    vendor_id: str,
    raw_items: list[Any],
) -> tuple[list[dict[str, Any]], int]:
    if not raw_items:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="At least one item is required")

    normalized_items: list[dict[str, Any]] = []
    computed_total = 0
    for item in raw_items:
        qty = int(getattr(item, "qty", 0) or 0)
        if qty <= 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Item qty must be >= 1")
        item_id = str(getattr(item, "item_id", "") or "").strip()
        if not item_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="item_id is required")

        unit_price_paise, canonical_title = await _lookup_item_unit_price_paise(
            db,
            vendor_id=vendor_id,
            item_id=item_id,
        )
        line_total = qty * unit_price_paise
        normalized_items.append(
            {
                "item_id": item_id,
                "title": str(getattr(item, "title", None) or canonical_title),
                "qty": qty,
                "unit_price_paise": unit_price_paise,
                "total_price_paise": line_total,
                "meta": dict(getattr(item, "meta", {}) or {}),
            }
        )
        computed_total += line_total
    return normalized_items, computed_total


def _enforce_total_tamper_threshold(client_total: Optional[int], server_total: int) -> None:
    if client_total is None:
        return
    if server_total <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Server-computed total is invalid")
    diff_ratio = abs(int(client_total) - int(server_total)) / float(server_total)
    if diff_ratio > 0.01:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Client total mismatch. client_total_amount_paise={int(client_total)}, server_total_amount_paise={int(server_total)}",
        )


async def _compute_service_amount_paise(
    db,
    *,
    vendor_id: str,
    package_id: str,
    event_date: str,
) -> tuple[int, dict[str, Any]]:
    package = await db.packages.find_one(
        {"id": package_id, "vendor_id": vendor_id, "is_active": {"$ne": False}},
        {"_id": 0, "price": 1, "name": 1},
    )
    if not package:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found for vendor")

    base_amount_rupees = float(package.get("price") or 0)
    if base_amount_rupees <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid package price")

    vendor_doc = await db.vendors.find_one({"id": vendor_id}, {"_id": 0, "pricing_rules": 1})
    pricing_rules = (vendor_doc or {}).get("pricing_rules") or []
    pricing_preview = apply_pricing_rules(base_amount_rupees, event_date, pricing_rules)
    amount_paise = _to_paise(pricing_preview.get("total"))
    if amount_paise <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid computed service amount")
    return amount_paise, pricing_preview


async def _lookup_rental_daily_base_price_paise(
    db,
    *,
    vendor_id: str,
    item_id: str,
) -> tuple[int, str]:
    vendor = await db.vendors.find_one(
        {"id": vendor_id, "is_active": True},
        {"_id": 0, "base_price": 1, "details.rental_items": 1},
    )
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found or inactive")

    rental_items = ((vendor.get("details") or {}).get("rental_items") or [])
    for item in rental_items:
        if str(item.get("id") or item.get("item_id") or "") == item_id:
            daily_paise = int(item.get("daily_price_paise") or _to_paise(item.get("daily_price") or item.get("price") or item.get("unit_price")))
            if daily_paise > 0:
                return daily_paise, str(item.get("name") or "Rental Item")

    fallback_paise = _to_paise(vendor.get("base_price"))
    if fallback_paise <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Rental base price not configured")
    return fallback_paise, "Rental Item"


def _rental_days_inclusive(check_in_date: str, check_out_date: str) -> int:
    check_in = _parse_iso_date(check_in_date)
    check_out = _parse_iso_date(check_out_date)
    days = (check_out - check_in).days + 1
    if days <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid rental day range")
    return days


def _compute_rental_deposit(total_amount_paise: int) -> tuple[int, int]:
    deposit = int(round(total_amount_paise * 0.3))
    balance = max(total_amount_paise - deposit, 0)
    return deposit, balance


def _rental_refund_amounts(meta: dict[str, Any], now):
    deposit_paise = int(meta.get("deposit_amount_paise", 0) or 0)
    total_paise = int(meta.get("total_amount_paise", 0) or 0) or int(meta.get("total_amount", 0) or 0)
    check_in = meta.get("check_in_date")
    if check_in:
        try:
            event_at = datetime.fromisoformat(f"{check_in}T00:00:00+05:30").astimezone(tz=utcnow().tzinfo)
            hours_left = (event_at - now).total_seconds() / 3600
        except Exception:
            hours_left = 9999
    else:
        hours_left = 9999

    if hours_left < 0:
        return 0, 0
    refund = deposit_paise // 2 if deposit_paise > 0 else 0
    return refund, total_paise - refund


def _refund_amount_with_fee(amount_paise: int, event_at, now):
    hours_left = (event_at - now).total_seconds() / 3600
    if hours_left >= 48:
        return amount_paise, 0
    fee = (amount_paise * 25) // 100
    return max(amount_paise - fee, 0), fee


async def _enforce_booking_access(request: Request, booking: dict[str, Any], current_user: dict[str, Any]) -> None:
    db = get_db_from_request(request)
    role = _normalize_role(current_user.get("role"))
    if role == UserRole.ADMIN.value:
        return
    if role == UserRole.VENDOR.value:
        vendor = await db.vendors.find_one({"id": booking.get("vendor_id")}, {"_id": 0, "user_id": 1})
        enforce_vendor_or_admin(
            current_user=current_user,
            vendor_user_id=(vendor or {}).get("user_id"),
            resource_name="booking",
        )
        return
    enforce_owner_or_admin(
        current_user=current_user,
        owner_user_id=booking.get("user_id"),
        resource_name="booking",
    )
