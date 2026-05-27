from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pymongo import ReturnDocument

from core.config import get_settings
from core.database import get_db_from_request
from core.security import get_current_user
from booking_engine.lock_service import release_lock
from canonical_models.common import BookingIntentStatus, CategoryType, ResponseEnvelope, UserRole, utcnow

router = APIRouter(prefix="/api/grocery", tags=["grocery"])
settings = get_settings()


class ReserveItemInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_id: str = Field(min_length=3)
    qty: int = Field(ge=1, le=5000)


class ReserveCartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vendor_id: str = Field(min_length=3)
    items: list[ReserveItemInput] = Field(min_length=1, max_length=100)


class ReserveCartResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lock_id: str
    expires_at: datetime
    total_amount_paise: int
    items: list[dict[str, Any]]


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lock_id: str = Field(min_length=8)
    idempotency_key: str = Field(min_length=8, max_length=128)
    delivery_address: str = Field(min_length=10, max_length=500)
    notes: Optional[str] = None


class CheckoutResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    booking_intent_id: str
    razorpay_order_id: str
    amount_paise: int
    currency: str = "INR"
    key_id: str
    lock_expires_at: datetime


class GroceryOrderStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str = Field(pattern="^(PROCESSING|SHIPPED)$")
    tracking_info: Optional[dict[str, Any]] = None


class GroceryItemCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=200)
    category: Optional[str] = None
    unit: str = Field(default="kg", min_length=1, max_length=20)
    unit_price: Optional[float] = None
    unit_price_paise: Optional[int] = None
    stock_qty: Optional[int] = None
    total_qty: Optional[int] = None
    is_available: bool = True
    image_url: Optional[str] = None


class GroceryItemUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    category: Optional[str] = None
    unit: Optional[str] = Field(default=None, min_length=1, max_length=20)
    unit_price: Optional[float] = None
    unit_price_paise: Optional[int] = None
    stock_qty: Optional[int] = None
    total_qty: Optional[int] = None
    is_available: Optional[bool] = None
    image_url: Optional[str] = None


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


def _normalize_role(raw_role: str | None) -> str:
    role = str(raw_role or "").lower()
    if role == "user":
        return UserRole.CUSTOMER.value
    return role


def _payment_client_from_app(request: Request):
    client = getattr(request.app.state, "razorpay_client", None)
    if client is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Payment provider unavailable")
    return client


def _to_unit_price_paise(item_doc: dict[str, Any]) -> int:
    if isinstance(item_doc.get("unit_price_paise"), int):
        return int(item_doc["unit_price_paise"])
    raw_rupees = item_doc.get("unit_price")
    if raw_rupees is None:
        return 0
    try:
        return int(round(float(raw_rupees) * 100))
    except Exception:
        return 0


async def _resolve_vendor_id_for_user(db, current_user: dict[str, Any]) -> str:
    vendor = await db.vendors.find_one({"user_id": str(current_user.get("id"))}, {"_id": 0, "id": 1})
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor profile not found")
    return str(vendor["id"])


async def _release_expired_locks_for_user(db, user_id: str) -> None:
    now = utcnow()
    expired = await db.resource_locks.find(
        {
            "status": "ACTIVE",
            "user_id": user_id,
            "expires_at": {"$lte": now},
            "entity_type": "STOCK",
        },
        {"_id": 0},
    ).to_list(length=200)

    for lock in expired:
        for item in lock.get("items", []):
            await db.grocery_items.update_one(
                {"id": item.get("item_id"), "vendor_id": lock.get("vendor_id")},
                {
                    "$inc": {"reserved_qty": -int(item.get("qty", 0) or 0)},
                    "$set": {"updated_at": now},
                },
            )
        await db.resource_locks.update_one(
            {"id": lock["id"], "status": "ACTIVE"},
            {"$set": {"status": "EXPIRED", "released_at": now}},
        )


@router.get("/vendors", response_model=ResponseEnvelope[list[dict]])
async def list_grocery_vendors(request: Request):
    db = get_db_from_request(request)
    vendor_ids = await db.grocery_items.distinct("vendor_id", {"is_available": {"$ne": False}})
    query: dict[str, Any] = {"id": {"$in": vendor_ids}}
    vendors = await db.vendors.find(
        query,
        {
            "_id": 0,
            "id": 1,
            "business_name": 1,
            "city": 1,
            "rating": 1,
            "is_active": 1,
            "status": 1,
        },
    ).to_list(length=1000)
    filtered = [v for v in vendors if v.get("is_active", True)]
    return ResponseEnvelope[list[dict]](
        success=True,
        data=filtered,
        message="Grocery vendors fetched",
        request_id=_request_id(request),
    )


@router.get("/vendors/{vendor_id}/items", response_model=ResponseEnvelope[list[dict]])
async def list_vendor_items(vendor_id: str, request: Request):
    db = get_db_from_request(request)
    items = await db.grocery_items.find(
        {"vendor_id": vendor_id, "is_available": {"$ne": False}},
        {"_id": 0},
    ).to_list(length=2000)
    return ResponseEnvelope[list[dict]](
        success=True,
        data=items,
        message="Vendor grocery items fetched",
        request_id=_request_id(request),
    )


@router.post("/vendor/items", response_model=ResponseEnvelope[dict])
async def add_vendor_item(
    request: Request,
    payload: GroceryItemCreateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    role = _normalize_role(current_user.get("role"))
    if role not in {UserRole.VENDOR.value, UserRole.ADMIN.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vendor or admin only")

    vendor_id = await _resolve_vendor_id_for_user(db, current_user) if role == UserRole.VENDOR.value else str(
        current_user.get("vendor_id") or ""
    )
    if not vendor_id and role == UserRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="vendor_id required for admin")

    unit_price_paise = payload.unit_price_paise
    if unit_price_paise is None and payload.unit_price is not None:
        unit_price_paise = int(round(float(payload.unit_price) * 100))
    unit_price_paise = int(unit_price_paise or 0)

    now = utcnow()
    item_doc = {
        "id": f"gitem_{uuid4().hex}",
        "vendor_id": vendor_id,
        "name": payload.name,
        "category": payload.category,
        "unit": payload.unit,
        "unit_price": float(payload.unit_price) if payload.unit_price is not None else None,
        "unit_price_paise": unit_price_paise,
        "stock_qty": int(payload.stock_qty or 0),
        "total_qty": int(payload.total_qty or payload.stock_qty or 0),
        "reserved_qty": 0,
        "sold_qty": 0,
        "is_available": bool(payload.is_available),
        "image_url": payload.image_url,
        "created_at": now,
        "updated_at": now,
    }
    await db.grocery_items.insert_one(item_doc)
    return ResponseEnvelope[dict](
        success=True,
        data=item_doc,
        message="Grocery item created",
        request_id=_request_id(request),
    )


@router.put("/vendor/items/{item_id}", response_model=ResponseEnvelope[dict])
async def update_vendor_item(
    item_id: str,
    request: Request,
    payload: GroceryItemUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    role = _normalize_role(current_user.get("role"))
    if role not in {UserRole.VENDOR.value, UserRole.ADMIN.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vendor or admin only")

    item = await db.grocery_items.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if role == UserRole.VENDOR.value:
        vendor_id = await _resolve_vendor_id_for_user(db, current_user)
        if item.get("vendor_id") != vendor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    update = payload.model_dump(exclude_unset=True)
    if "unit_price" in update and update.get("unit_price") is not None and update.get("unit_price_paise") is None:
        update["unit_price_paise"] = int(round(float(update["unit_price"]) * 100))
    update["updated_at"] = utcnow()

    updated = await db.grocery_items.find_one_and_update(
        {"id": item_id},
        {"$set": update},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Update conflict")

    return ResponseEnvelope[dict](
        success=True,
        data=updated,
        message="Grocery item updated",
        request_id=_request_id(request),
    )


@router.delete("/vendor/items/{item_id}", response_model=ResponseEnvelope[dict])
async def delete_vendor_item(
    item_id: str,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    role = _normalize_role(current_user.get("role"))
    if role not in {UserRole.VENDOR.value, UserRole.ADMIN.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vendor or admin only")

    item = await db.grocery_items.find_one({"id": item_id}, {"_id": 0, "vendor_id": 1})
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if role == UserRole.VENDOR.value:
        vendor_id = await _resolve_vendor_id_for_user(db, current_user)
        if item.get("vendor_id") != vendor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    await db.grocery_items.delete_one({"id": item_id})
    return ResponseEnvelope[dict](
        success=True,
        data={"deleted": True, "id": item_id},
        message="Grocery item deleted",
        request_id=_request_id(request),
    )


@router.post("/cart/reserve", response_model=ResponseEnvelope[ReserveCartResponse])
async def reserve_cart(
    request: Request,
    payload: ReserveCartRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    now = utcnow()
    user_id = str(current_user.get("id"))
    await _release_expired_locks_for_user(db, user_id)

    if _normalize_role(current_user.get("role")) not in {UserRole.CUSTOMER.value, UserRole.ADMIN.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only customers can reserve cart items")

    reserved_rollbacks: list[tuple[str, int]] = []
    lock_items: list[dict[str, Any]] = []
    total_amount_paise = 0

    try:
        for row in payload.items:
            item_doc = await db.grocery_items.find_one(
                {"id": row.item_id, "vendor_id": payload.vendor_id, "is_available": {"$ne": False}},
                {
                    "_id": 0,
                    "id": 1,
                    "name": 1,
                    "vendor_id": 1,
                    "stock_qty": 1,
                    "total_qty": 1,
                    "reserved_qty": 1,
                    "sold_qty": 1,
                    "unit_price": 1,
                    "unit_price_paise": 1,
                },
            )
            if not item_doc:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item not found: {row.item_id}")

            # Atomic reserve guard:
            # available = (total_qty or stock_qty) - reserved_qty - sold_qty
            updated = await db.grocery_items.find_one_and_update(
                {
                    "id": row.item_id,
                    "vendor_id": payload.vendor_id,
                    "$expr": {
                        "$gte": [
                            {
                                "$subtract": [
                                    {
                                        "$subtract": [
                                            {"$ifNull": ["$total_qty", {"$ifNull": ["$stock_qty", 0]}]},
                                            {"$ifNull": ["$reserved_qty", 0]},
                                        ]
                                    },
                                    {"$ifNull": ["$sold_qty", 0]},
                                ]
                            },
                            row.qty,
                        ]
                    },
                },
                {"$inc": {"reserved_qty": row.qty}, "$set": {"updated_at": now}},
                projection={"_id": 0, "id": 1},
            )
            if not updated:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insufficient stock for item: {row.item_id}",
                )

            reserved_rollbacks.append((row.item_id, row.qty))
            unit_price_paise = _to_unit_price_paise(item_doc)
            line_total = unit_price_paise * row.qty
            total_amount_paise += line_total
            available_qty = (
                int(item_doc.get("total_qty", item_doc.get("stock_qty", 0)) or 0)
                - int(item_doc.get("reserved_qty", 0) or 0)
                - int(item_doc.get("sold_qty", 0) or 0)
            )
            lock_items.append(
                {
                    "item_id": row.item_id,
                    "title": item_doc.get("name", "Item"),
                    "qty": row.qty,
                    "unit_price_paise": unit_price_paise,
                    "total_price_paise": line_total,
                    "available_qty_at_lock": max(available_qty, 0),
                }
            )

        lock_id = f"lock_{uuid4().hex}"
        lock_doc = {
            "id": lock_id,
            "entity_type": "STOCK",
            "entity_id": f"cart:{user_id}:{uuid4().hex[:12]}",
            "booking_intent_id": None,
            "locked_qty": sum(i["qty"] for i in lock_items),
            "status": "ACTIVE",
            "vendor_id": payload.vendor_id,
            "user_id": user_id,
            "items": lock_items,
            "total_amount_paise": total_amount_paise,
            "expires_at": now + timedelta(minutes=15),
            "released_at": None,
            "created_at": now,
        }
        await db.resource_locks.insert_one(lock_doc)
    except Exception:
        for item_id, qty in reserved_rollbacks:
            await db.grocery_items.update_one(
                {"id": item_id, "vendor_id": payload.vendor_id},
                {"$inc": {"reserved_qty": -qty}, "$set": {"updated_at": utcnow()}},
            )
        raise

    return ResponseEnvelope[ReserveCartResponse](
        success=True,
        data=ReserveCartResponse(
            lock_id=lock_id,
            expires_at=lock_doc["expires_at"],
            total_amount_paise=total_amount_paise,
            items=lock_items,
        ),
        message="Cart reserved",
        request_id=_request_id(request),
    )


@router.delete("/cart/reserve/{lock_id}", response_model=ResponseEnvelope[dict])
async def release_cart_lock(
    lock_id: str,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    lock = await db.resource_locks.find_one({"id": lock_id}, {"_id": 0})
    if not lock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lock not found")

    role = _normalize_role(current_user.get("role"))
    if role != UserRole.ADMIN.value and str(lock.get("user_id")) != str(current_user.get("id")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this lock")

    if lock.get("status") != "ACTIVE":
        return ResponseEnvelope[dict](
            success=True,
            data={"released": False, "status": lock.get("status")},
            message="Lock already inactive",
            request_id=_request_id(request),
        )

    now = utcnow()
    _ = now
    await release_lock(db, lock_id)

    return ResponseEnvelope[dict](
        success=True,
        data={"released": True, "lock_id": lock_id},
        message="Lock released",
        request_id=_request_id(request),
    )


@router.get("/cart/reserve/{lock_id}", response_model=ResponseEnvelope[dict])
async def get_cart_lock_status(
    lock_id: str,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    lock = await db.resource_locks.find_one({"id": lock_id, "entity_type": "STOCK"}, {"_id": 0})
    if not lock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lock not found")

    role = _normalize_role(current_user.get("role"))
    user_id = str(current_user.get("id"))
    if role != UserRole.ADMIN.value and str(lock.get("user_id")) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this lock")

    now = utcnow()
    expires_at = lock.get("expires_at")
    is_valid = bool(lock.get("status") == "ACTIVE" and expires_at and expires_at > now)
    return ResponseEnvelope[dict](
        success=True,
        data={
            "lock_id": lock_id,
            "expires_at": expires_at,
            "is_valid": is_valid,
            "items": lock.get("items", []),
        },
        message="Cart lock status fetched",
        request_id=_request_id(request),
    )


@router.post("/checkout", response_model=ResponseEnvelope[CheckoutResponse])
async def checkout_grocery(
    request: Request,
    payload: CheckoutRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    user_id = str(current_user.get("id"))

    lock = await db.resource_locks.find_one(
        {"id": payload.lock_id, "entity_type": "STOCK"},
        {"_id": 0},
    )
    if not lock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lock not found")
    if str(lock.get("user_id")) != user_id and _normalize_role(current_user.get("role")) != UserRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this lock")
    if lock.get("status") != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Lock is not active")
    if lock.get("expires_at") and lock["expires_at"] <= utcnow():
        for item in lock.get("items", []):
            await db.grocery_items.update_one(
                {"id": item.get("item_id"), "vendor_id": lock.get("vendor_id")},
                {"$inc": {"reserved_qty": -int(item.get("qty", 0) or 0)}, "$set": {"updated_at": utcnow()}},
            )
        await db.resource_locks.update_one(
            {"id": payload.lock_id, "status": "ACTIVE"},
            {"$set": {"status": "EXPIRED", "released_at": utcnow()}},
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Lock expired")

    existing_intent = await db.booking_intents.find_one({"idempotency_key": payload.idempotency_key}, {"_id": 0})
    if existing_intent:
        existing_payment = await db.payments.find_one(
            {"booking_intent_id": existing_intent["id"], "status": {"$in": ["CREATED", "CLIENT_VERIFIED", "CONFIRMED"]}},
            {"_id": 0, "razorpay_order_id": 1, "amount": 1, "currency": 1},
        )
        if not existing_payment:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Intent exists without active payment")
        return ResponseEnvelope[CheckoutResponse](
            success=True,
            data=CheckoutResponse(
                booking_intent_id=existing_intent["id"],
                razorpay_order_id=existing_payment["razorpay_order_id"],
                amount_paise=int(existing_payment.get("amount", 0)),
                currency=existing_payment.get("currency", "INR"),
                key_id=settings.RAZORPAY_KEY_ID,
                lock_expires_at=lock.get("expires_at"),
            ),
            message="Idempotent checkout replay",
            request_id=_request_id(request),
        )

    intent_id = f"bint_{uuid4().hex}"
    now = utcnow()
    intent_doc = {
        "id": intent_id,
        "idempotency_key": payload.idempotency_key,
        "user_id": user_id,
        "vendor_id": lock["vendor_id"],
        "category_type": CategoryType.GROCERY.value,
        "items": lock.get("items", []),
        "total_amount_paise": int(lock.get("total_amount_paise", 0) or 0),
        "scheduled_at": None,
        "duration_minutes": None,
        "notes": payload.notes,
        "meta": {
            "delivery_address": payload.delivery_address,
            "resource_lock_ids": [payload.lock_id],
        },
        "status": BookingIntentStatus.PENDING.value,
        "expires_at": now + timedelta(minutes=30),
        "created_at": now,
        "updated_at": now,
        "version": 1,
    }
    await db.booking_intents.insert_one(intent_doc)
    await db.resource_locks.update_one(
        {"id": payload.lock_id, "status": "ACTIVE"},
        {"$set": {"booking_intent_id": intent_id}},
    )

    existing_payment = await db.payments.find_one(
        {"booking_intent_id": intent_id, "status": {"$in": ["CREATED", "CLIENT_VERIFIED", "CONFIRMED"]}},
        {"_id": 0, "razorpay_order_id": 1, "amount": 1, "currency": 1},
    )
    if existing_payment:
        razorpay_order_id = existing_payment["razorpay_order_id"]
        amount_paise = int(existing_payment.get("amount", 0))
    else:
        amount_paise = int(intent_doc.get("total_amount_paise", 0) or 0)
        if amount_paise <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid checkout amount")

        razorpay_client = _payment_client_from_app(request)
        razorpay_order = razorpay_client.order.create(
            {
                "amount": amount_paise,
                "currency": "INR",
                "receipt": intent_id,
                "notes": {"booking_intent_id": intent_id, "lock_id": payload.lock_id, "category_type": "grocery"},
            }
        )
        razorpay_order_id = razorpay_order["id"]
        payment_doc = {
            "id": f"pay_{uuid4().hex}",
            "booking_intent_id": intent_id,
            "booking_id": None,
            "amount": amount_paise,
            "currency": "INR",
            "status": "CREATED",
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": None,
            "razorpay_signature": None,
            "idempotency_key": f"{intent_id}:{razorpay_order_id}",
            "created_at": now,
            "updated_at": now,
        }
        await db.payments.insert_one(payment_doc)

    return ResponseEnvelope[CheckoutResponse](
        success=True,
        data=CheckoutResponse(
            booking_intent_id=intent_id,
            razorpay_order_id=razorpay_order_id,
            amount_paise=amount_paise,
            currency="INR",
            key_id=settings.RAZORPAY_KEY_ID,
            lock_expires_at=lock.get("expires_at"),
        ),
        message="Checkout initiated",
        request_id=_request_id(request),
    )


@router.get("/orders/{order_id}", response_model=ResponseEnvelope[dict])
async def get_grocery_order(
    order_id: str,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    booking = await db.bookings.find_one({"id": order_id, "category_type": CategoryType.GROCERY.value}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grocery order not found")

    role = _normalize_role(current_user.get("role"))
    if role == UserRole.ADMIN.value:
        pass
    elif role == UserRole.VENDOR.value:
        vendor = await db.vendors.find_one({"id": booking.get("vendor_id")}, {"_id": 0, "user_id": 1})
        if not vendor or str(vendor.get("user_id")) != str(current_user.get("id")):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    else:
        if str(booking.get("user_id")) != str(current_user.get("id")):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    payment = await db.payments.find_one({"booking_id": booking["id"]}, {"_id": 0})
    data = {"booking": booking, "payment": payment}
    return ResponseEnvelope[dict](
        success=True,
        data=data,
        message="Grocery order fetched",
        request_id=_request_id(request),
    )


@router.get("/orders", response_model=ResponseEnvelope[list[dict]])
async def list_grocery_orders(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
    skip: int = 0,
    limit: int = 200,
):
    db = get_db_from_request(request)
    role = _normalize_role(current_user.get("role"))
    query: dict[str, Any] = {"category_type": CategoryType.GROCERY.value}

    if role == UserRole.ADMIN.value:
        pass
    elif role == UserRole.VENDOR.value:
        vendor = await db.vendors.find_one({"user_id": str(current_user.get("id"))}, {"_id": 0, "id": 1})
        if not vendor:
            return ResponseEnvelope[list[dict]](
                success=True,
                data=[],
                message="No vendor profile found",
                request_id=_request_id(request),
            )
        query["vendor_id"] = vendor["id"]
    else:
        query["user_id"] = str(current_user.get("id"))

    cursor = db.bookings.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)
    return ResponseEnvelope[list[dict]](
        success=True,
        data=items,
        message="Grocery orders fetched",
        request_id=_request_id(request),
    )


@router.post("/orders/{order_id}/update-status", response_model=ResponseEnvelope[dict])
async def update_grocery_order_status(
    order_id: str,
    payload: GroceryOrderStatusUpdateRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    role = _normalize_role(current_user.get("role"))
    if role not in {UserRole.VENDOR.value, UserRole.ADMIN.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vendor or admin only")

    booking = await db.bookings.find_one({"id": order_id, "category_type": CategoryType.GROCERY.value}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grocery order not found")

    if role == UserRole.VENDOR.value:
        vendor = await db.vendors.find_one({"id": booking.get("vendor_id")}, {"_id": 0, "user_id": 1})
        if not vendor or str(vendor.get("user_id")) != str(current_user.get("id")):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    meta = booking.get("meta") or {}
    current_fulfillment = str(meta.get("fulfillment_status") or "CONFIRMED")
    target = payload.status.upper()
    allowed = {"CONFIRMED": {"PROCESSING"}, "PROCESSING": {"SHIPPED"}}
    if target not in allowed.get(current_fulfillment, set()) and role != UserRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid fulfillment transition")

    new_meta = {
        **meta,
        "fulfillment_status": target,
        "tracking_info": payload.tracking_info if target == "SHIPPED" else (meta.get("tracking_info") or {}),
        "fulfillment_updated_at": utcnow(),
    }
    updated = await db.bookings.find_one_and_update(
        {
            "id": order_id,
            "version": int(booking.get("version", 1)),
        },
        {
            "$set": {
                "meta": new_meta,
                "updated_at": utcnow(),
            },
            "$inc": {"version": 1},
        },
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflict: stale booking version")

    return ResponseEnvelope[dict](
        success=True,
        data=updated,
        message="Grocery order status updated",
        request_id=_request_id(request),
    )


@router.put("/orders/{order_id}/status", response_model=ResponseEnvelope[dict])
async def update_grocery_order_status_alias(
    order_id: str,
    payload: GroceryOrderStatusUpdateRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    return await update_grocery_order_status(order_id, payload, request, current_user)


@router.get("/orders/{order_id}/track", response_model=ResponseEnvelope[dict])
async def track_grocery_order(order_id: str, request: Request):
    db = get_db_from_request(request)
    booking = await db.bookings.find_one(
        {"id": order_id, "category_type": CategoryType.GROCERY.value},
        {"_id": 0, "id": 1, "status": 1, "meta": 1, "created_at": 1, "updated_at": 1},
    )
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grocery order not found")

    meta = booking.get("meta") or {}
    data = {
        "order_id": booking.get("id"),
        "booking_status": booking.get("status"),
        "fulfillment_status": meta.get("fulfillment_status", "CONFIRMED"),
        "tracking_info": meta.get("tracking_info") or {},
        "created_at": booking.get("created_at"),
        "updated_at": booking.get("updated_at"),
    }
    return ResponseEnvelope[dict](
        success=True,
        data=data,
        message="Grocery order tracking fetched",
        request_id=_request_id(request),
    )
