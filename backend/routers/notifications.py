from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import Optional
from datetime import datetime, timezone
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, ConfigDict, Field

from auth import get_current_user, get_current_user_optional
from api.deps import get_db
from canonical_models.common import ResponseEnvelope, UserRole
from email_service import (
    send_welcome_email,
    send_quote_received_email,
    send_booking_confirmation_email,
    send_vendor_new_quote_request,
)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)


class BulkDeleteRequest(BaseModel):
    ids: list[str] = Field(min_length=1)


class NotificationItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    title: str
    message: str
    notification_type: str | None = None
    is_read: bool = False
    created_at: datetime


def _current_user_id(current_user: dict) -> str:
    return str(current_user.get("id") or current_user.get("sub") or "")


def _current_user_role(current_user: dict) -> str:
    role = str(current_user.get("role") or "").lower()
    if role == "user":
        return UserRole.CUSTOMER.value
    return role


def _make_id():
    return str(int(datetime.now(timezone.utc).timestamp() * 1000))


@router.post("/email")
async def send_email_notification(
    payload: dict,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Send an email notification or queue it in the DB.

    Expected payload examples:
    - {"user_id": "u123", "template_id": "BOOKING_CREATED", "data": {...}}
    - {"to_email": "a@b.com", "title": "Subject", "message": "Body"}
    """
    user_id = payload.get("user_id")
    template_id = payload.get("template_id")
    data = payload.get("data") or {}
    to_email = payload.get("to_email")

    # Resolve email if user_id provided
    if user_id and not to_email:
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        to_email = user.get("email") if user else None

    notif = {
        "id": _make_id(),
        "channel": "email",
        "to": to_email,
        "user_id": user_id,
        "template_id": template_id,
        "data": data,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "queued",
    }

    try:
        await db.notifications.insert_one(notif)
    except Exception as e:
        logger.error(f"Failed to persist notification: {e}")

    # Try best-effort send for known templates
    sent = False
    try:
        if template_id == 'WELCOME' and to_email:
            await send_welcome_email(to_email, data.get('user_name') or '')
            sent = True
        elif template_id == 'QUOTE_RECEIVED' and to_email:
            await send_quote_received_email(to_email, data.get('user_name', ''), data.get('vendor_name', ''), data.get('quoted_price', 0))
            sent = True
        elif template_id == 'BOOKING_CREATED' and to_email:
            # expects order_id, total_amount, vendor_name, user_name
            await send_booking_confirmation_email(to_email, data.get('user_name', ''), data.get('vendor_name', ''), data.get('order_id', ''), data.get('total_amount', 0))
            sent = True
        elif template_id == 'VENDOR_NEW_QUOTE_REQUEST' and to_email:
            await send_vendor_new_quote_request(to_email, data.get('vendor_name', ''), data.get('user_name', ''), data.get('services', []))
            sent = True
    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")

    # Update status
    try:
        await db.notifications.update_one({"id": notif["id"]}, {"$set": {"status": sent and 'sent' or 'queued'}})
    except Exception:
        pass

    return {"status": "ok", "sent": sent, "id": notif["id"]}


@router.post("/sms")
async def send_sms_notification(
    payload: dict,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Queue an SMS notification. (No SMS gateway configured — queued only)"""
    phone = payload.get("phone")
    message = payload.get("message")

    if not phone or not message:
        raise HTTPException(status_code=400, detail="phone and message are required")

    notif = {
        "id": _make_id(),
        "channel": "sms",
        "to": phone,
        "message": message,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "queued",
    }
    try:
        await db.notifications.insert_one(notif)
    except Exception as e:
        logger.error(f"Failed to persist SMS notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue SMS")

    # No external SMS gateway configured — return queued
    return {"status": "ok", "queued": True, "id": notif["id"]}


@router.get("", response_model=ResponseEnvelope[list[NotificationItem]])
async def list_notifications(
    request: Request,
    user_id: Optional[str] = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """List notifications scoped to authenticated user; admins can query any user."""
    role = _current_user_role(current_user)
    current_user_id = _current_user_id(current_user)
    effective_user_id = current_user_id

    if user_id and user_id != current_user_id:
        if role != UserRole.ADMIN.value:
            raise HTTPException(status_code=403, detail="Admin access required for cross-user notifications")
        effective_user_id = user_id

    query = {"user_id": effective_user_id}
    cursor = db.notifications.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    items = await cursor.to_list(limit)
    normalized: list[NotificationItem] = []
    for item in items:
        created_at = item.get("created_at")
        if isinstance(created_at, str):
            try:
                item["created_at"] = datetime.fromisoformat(created_at)
            except Exception:
                item["created_at"] = datetime.now(timezone.utc)
        elif not isinstance(created_at, datetime):
            item["created_at"] = datetime.now(timezone.utc)
        normalized.append(NotificationItem.model_validate(item))
    return ResponseEnvelope[list[NotificationItem]](
        success=True,
        data=normalized,
        message="Notifications fetched",
        request_id=getattr(request.state, "request_id", ""),
    )


@router.delete("")
async def bulk_delete_notifications(
    payload: BulkDeleteRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Delete notifications by ids for current user only."""
    ids = list(dict.fromkeys(payload.ids))
    owner_id = _current_user_id(current_user)
    owned_count = await db.notifications.count_documents(
        {"id": {"$in": ids}, "user_id": owner_id}
    )
    if owned_count != len(ids):
        raise HTTPException(status_code=403, detail="One or more notifications are not owned by current user")

    result = await db.notifications.delete_many({"id": {"$in": ids}, "user_id": owner_id})
    return {"deleted": result.deleted_count}
