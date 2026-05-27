"""Booking CRUD, action state machine, cancellation, and query routes."""
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pymongo import ReturnDocument
from starlette.concurrency import run_in_threadpool

from canonical_models.booking import BookingActionRequest
from canonical_models.common import BookingAction, BookingStatus, ResponseEnvelope, UserRole, utcnow
from core.database import get_db_from_request

from .helpers import (
    BookingCancelRequest, BookingDetail, BookingListItem, BookingOrderBridgeResponse,
    BookingOrderLinkRequest, BookingTransitionItem, BOOKING_TRANSITIONS, ROLE_ALLOWED_ACTIONS,
    _allowed_actions_for_status, _enforce_booking_access, _enforce_booking_actor_access,
    _fetch_booking_any_or_404, _fetch_booking_or_404, _normalize_role, _payment_client_from_app,
    _request_id, _resolve_next_status, _to_booking_detail, _to_booking_list_item,
    get_current_user, handle_booking_action, limiter, require_admin,
)

router = APIRouter()


@router.get("/{booking_id}", response_model=ResponseEnvelope[BookingDetail])
async def get_booking(
    booking_id: str,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    booking = await _fetch_booking_or_404(db, booking_id)
    await _enforce_booking_access(request, booking, current_user)
    return ResponseEnvelope[BookingDetail](
        success=True,
        data=_to_booking_detail(booking),
        message="Booking fetched",
        request_id=_request_id(request),
    )


@router.get("/", response_model=ResponseEnvelope[list[BookingListItem]])
async def list_bookings(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
    status_filter: Optional[BookingStatus] = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
):
    db = get_db_from_request(request)
    role = _normalize_role(current_user.get("role"))
    query: dict[str, Any] = {}
    if status_filter:
        query["status"] = status_filter.value

    if role == UserRole.CUSTOMER.value:
        query["user_id"] = str(current_user.get("id"))
    elif role == UserRole.VENDOR.value:
        vendor = await db.vendors.find_one({"user_id": str(current_user.get("id"))}, {"_id": 0, "id": 1})
        if not vendor:
            return ResponseEnvelope[list[BookingListItem]](
                success=True,
                data=[],
                message="No vendor profile found",
                request_id=_request_id(request),
            )
        query["vendor_id"] = vendor["id"]

    cursor = db.bookings.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)
    typed = [_to_booking_list_item(item) for item in items]
    return ResponseEnvelope[list[BookingListItem]](
        success=True,
        data=typed,
        message="Bookings fetched",
        request_id=_request_id(request),
    )


@router.get("/vendor", response_model=ResponseEnvelope[list[BookingListItem]])
async def list_vendor_bookings(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
    status_filter: Optional[BookingStatus] = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
):
    db = get_db_from_request(request)
    role = _normalize_role(current_user.get("role"))
    if role != UserRole.VENDOR.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vendor role required")

    vendor = await db.vendors.find_one({"user_id": str(current_user.get("id"))}, {"_id": 0, "id": 1})
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor profile not found")

    query: dict[str, Any] = {"vendor_id": vendor["id"]}
    if status_filter:
        query["status"] = status_filter.value
    items = await db.bookings.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    typed = [_to_booking_list_item(item) for item in items]
    return ResponseEnvelope[list[BookingListItem]](
        success=True,
        data=typed,
        message="Vendor bookings fetched",
        request_id=_request_id(request),
    )


@router.post("/{booking_id}/action", response_model=ResponseEnvelope[dict])
async def booking_action(
    booking_id: str,
    request: Request,
    payload: BookingActionRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    updated = await handle_booking_action(
        request=request,
        booking_id=booking_id,
        payload=payload,
        current_user=current_user,
    )
    return ResponseEnvelope[dict](
        success=True,
        data=updated,
        message="Booking action applied",
        request_id=_request_id(request),
    )


@router.get("/{booking_id}/allowed-actions", response_model=ResponseEnvelope[list[str]])
async def get_allowed_actions(
    booking_id: str,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    _, booking = await _fetch_booking_any_or_404(db, booking_id)
    await _enforce_booking_actor_access(db, booking, current_user)
    role = _normalize_role(current_user.get("role"))
    current_status = str(booking.get("status") or "")
    actions = _allowed_actions_for_status(current_status=current_status, role=role)
    return ResponseEnvelope[list[str]](
        success=True,
        data=actions,
        message="Allowed booking actions fetched",
        request_id=_request_id(request),
    )


@router.get("/{booking_id}/order", response_model=ResponseEnvelope[BookingOrderBridgeResponse])
async def get_booking_order_bridge(
    booking_id: str,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    booking = await _fetch_booking_or_404(db, booking_id)
    await _enforce_booking_access(request, booking, current_user)
    legacy_order_id = booking.get("legacy_order_id") or (booking.get("meta") or {}).get("legacy_order_id")
    if not legacy_order_id:
        legacy_order = await db.orders.find_one({"booking_id": booking_id}, {"_id": 0, "id": 1})
        legacy_order_id = (legacy_order or {}).get("id")
    return ResponseEnvelope[BookingOrderBridgeResponse](
        success=True,
        data=BookingOrderBridgeResponse(booking_id=booking_id, order_id=legacy_order_id),
        message="Booking order bridge fetched",
        request_id=_request_id(request),
    )


@router.post("/{booking_id}/link-order", response_model=ResponseEnvelope[dict])
async def link_booking_order_bridge(
    booking_id: str,
    payload: BookingOrderLinkRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin()),
):
    db = get_db_from_request(request)
    booking = await _fetch_booking_or_404(db, booking_id)
    _ = booking
    order = await db.orders.find_one({"id": payload.order_id}, {"_id": 0, "id": 1})
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legacy order not found")
    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {"legacy_order_id": payload.order_id, "meta.legacy_order_id": payload.order_id, "updated_at": utcnow()}},
    )
    await db.orders.update_one(
        {"id": payload.order_id},
        {"$set": {"booking_id": booking_id, "updated_at": utcnow()}},
    )
    return ResponseEnvelope[dict](
        success=True,
        data={"booking_id": booking_id, "order_id": payload.order_id},
        message="Booking linked to legacy order",
        request_id=_request_id(request),
    )


@limiter.limit("10/hour")
@router.post("/{booking_id}/cancel", response_model=ResponseEnvelope[BookingDetail])
async def cancel_booking(
    booking_id: str,
    payload: BookingCancelRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    role = _normalize_role(current_user.get("role"))
    action = BookingAction.CANCEL.value
    request_id = _request_id(request)
    action_result: dict[str, Any] | None = None

    async with await db.client.start_session() as session:
        async with session.start_transaction():
            booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0}, session=session)
            if not booking:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

            await _enforce_booking_actor_access(db, booking, current_user)
            if action not in ROLE_ALLOWED_ACTIONS.get(role, set()):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role-action permission denied")

            current_version = int(booking.get("version", 1))
            if current_version != int(payload.expected_version):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflict: stale booking version")

            current_status = str(booking.get("status") or "")
            next_status = _resolve_next_status(current_status=current_status, action=action, role=role)
            now = utcnow()
            updated = await db.bookings.find_one_and_update(
                {"id": booking_id, "version": current_version, "status": current_status},
                {
                    "$set": {
                        "status": next_status,
                        "cancelled_at": now,
                        "cancellation_reason": payload.reason,
                        "updated_at": now,
                    },
                    "$inc": {"version": 1},
                },
                projection={"_id": 0},
                return_document=ReturnDocument.AFTER,
                session=session,
            )
            if not updated:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflict: stale state or version")

            payment = None
            if booking.get("payment_id"):
                payment = await db.payments.find_one({"id": booking["payment_id"]}, {"_id": 0}, session=session)
            if payment and payment.get("razorpay_payment_id"):
                refund_amount_paise = int(payment.get("amount", 0) or booking.get("amount_gross_paise", 0) or 0)
                razorpay_client = _payment_client_from_app(request)
                refund_response = await run_in_threadpool(
                    razorpay_client.payment.refund,
                    payment["razorpay_payment_id"],
                    {
                        "amount": refund_amount_paise,
                        "notes": {"booking_id": booking_id, "reason": payload.reason},
                    },
                )
                await db.refunds.insert_one(
                    {
                        "id": f"ref_{uuid4().hex}",
                        "booking_id": booking_id,
                        "payment_id": payment["id"],
                        "razorpay_refund_id": refund_response.get("id"),
                        "amount_paise": refund_amount_paise,
                        "status": "REQUESTED",
                        "reason": payload.reason,
                        "created_at": now,
                        "updated_at": now,
                    },
                    session=session,
                )
                await db.payments.update_one(
                    {"id": payment["id"]},
                    {
                        "$set": {
                            "status": "REFUNDED",
                            "razorpay_refund_id": refund_response.get("id"),
                            "refund_reason": payload.reason,
                            "updated_at": now,
                        }
                    },
                    session=session,
                )

            vendor_net_paise = int(booking.get("vendor_net_paise", 0) or 0)
            await db.vendor_ledger.update_one(
                {"vendor_id": booking["vendor_id"]},
                {
                    "$inc": {
                        "total_earned_paise": -vendor_net_paise,
                        "pending_payout_paise": -vendor_net_paise,
                    }
                },
                session=session,
            )

            if booking.get("resource_lock_ids"):
                await db.resource_locks.update_many(
                    {"id": {"$in": booking["resource_lock_ids"]}},
                    {"$set": {"status": "RELEASED", "released_at": now, "updated_at": now}},
                    session=session,
                )

            await db.state_transitions.insert_one(
                {
                    "entity_type": "BOOKING",
                    "entity_id": booking_id,
                    "collection": "bookings",
                    "from_status": current_status,
                    "to_status": next_status,
                    "actor_role": role,
                    "actor_id": str(current_user.get("id")),
                    "reason": payload.reason,
                    "created_at": now,
                },
                session=session,
            )
            await db.audit_logs.insert_one(
                {
                    "id": f"audit_{uuid4().hex}",
                    "actor_id": str(current_user.get("id")),
                    "actor_role": role,
                    "action": "booking_action_cancel",
                    "entity_type": "booking",
                    "entity_id": booking_id,
                    "payload": {
                        "collection": "bookings",
                        "from_status": current_status,
                        "to_status": next_status,
                        "expected_version": payload.expected_version,
                        "new_version": updated.get("version"),
                    },
                    "request_id": request_id,
                    "created_at": now,
                },
                session=session,
            )
            action_result = updated

    if action_result is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cancellation failed")

    return ResponseEnvelope[BookingDetail](
        success=True,
        data=_to_booking_detail(action_result),
        message="Booking cancelled",
        request_id=request_id,
    )


@router.get("/{booking_id}/transitions", response_model=ResponseEnvelope[list[BookingTransitionItem]])
async def get_booking_transitions(
    booking_id: str,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    booking = await _fetch_booking_or_404(db, booking_id)
    await _enforce_booking_access(request, booking, current_user)
    cursor = db.state_transitions.find(
        {"entity_type": "BOOKING", "entity_id": booking_id},
        {"_id": 0},
    ).sort("created_at", 1)
    transitions = await cursor.to_list(length=1000)
    typed = [BookingTransitionItem.model_validate(item) for item in transitions]
    return ResponseEnvelope[list[BookingTransitionItem]](
        success=True,
        data=typed,
        message="Booking transition history fetched",
        request_id=_request_id(request),
    )
