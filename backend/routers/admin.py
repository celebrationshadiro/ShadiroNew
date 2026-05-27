from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Literal, Optional, TypeVar
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument

from core.database import get_db_from_request
from core.security import get_current_user
from canonical_models.common import PayoutStatus, ResponseEnvelope, UserRole, utcnow
from models import VendorAdminPatch
from payments.execution_service import PaymentExecutionService

router = APIRouter(prefix="/api/admin", tags=["admin"])
T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)
    items: list[T]
    total: int
    skip: int
    limit: int


class VendorActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["approve", "reject", "suspend", "feature"]
    reason: Optional[str] = Field(default=None, max_length=500)


class UserActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["block", "activate"]
    reason: Optional[str] = Field(default=None, max_length=500)


class PayoutActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["approve", "reject"]
    reason: Optional[str] = Field(default=None, max_length=500)


class DisputeResolveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resolution: str = Field(min_length=3, max_length=2000)
    outcome: Literal["resolved_refund", "resolved_replacement", "resolved_warning", "resolved_rejected"] = "resolved_rejected"


class AdminRefundRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: Optional[str] = Field(default=None, max_length=500)


class AdminVendorListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    business_name: str
    status: Optional[str] = None
    category_id: Optional[str] = None
    city: Optional[str] = None
    created_at: Optional[datetime] = None
    owner_name: Optional[str] = None
    verification_status: Optional[str] = None


class AdminBookingListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: Optional[str] = None
    category_type: Optional[str] = None
    user_id: Optional[str] = None
    vendor_id: Optional[str] = None
    total_amount_paise: int = 0
    created_at: Optional[datetime] = None


class AdminUserListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: bool = True
    is_blocked: bool = False
    created_at: Optional[datetime] = None


class AdminPaymentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: Optional[str] = None
    amount_paise: int = 0
    booking_intent_id: Optional[str] = None
    user_id: Optional[str] = None
    created_at: Optional[datetime] = None


class AdminPayoutListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    vendor_id: Optional[str] = None
    amount: float = 0.0
    status: Optional[str] = None
    requested_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None


class AdminAuditLog(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    admin_id: Optional[str] = None
    action_type: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


async def require_admin(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    role = str(current_user.get("role", "")).lower()
    if role != UserRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


async def _admin_audit_log(
    *,
    db,
    admin_id: str,
    action: str,
    target_type: str,
    target_id: Optional[str],
    request_id: str,
    payload: dict[str, Any] | None = None,
) -> None:
    await db.admin_audit_logs.insert_one(
        {
            "id": f"aal_{uuid4().hex}",
            "admin_id": admin_id,
            "action_type": action,
            "target_type": target_type,
            "target_id": target_id,
            "payload": payload or {},
            "request_id": request_id,
            "created_at": utcnow(),
        }
    )


@router.get("/vendors", response_model=ResponseEnvelope[PaginatedResponse[AdminVendorListItem]])
async def list_vendors(
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    category_id: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> ResponseEnvelope[PaginatedResponse[AdminVendorListItem]]:
    db = get_db_from_request(request)
    query: dict[str, Any] = {}
    if status_filter:
        query["status"] = status_filter
    if category_id:
        query["category_id"] = category_id

    total = await db.vendors.count_documents(query)
    cursor = db.vendors.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    owner_user_ids = [str(v.get("user_id")) for v in docs if v.get("user_id")]
    owners_by_id: dict[str, str] = {}
    if owner_user_ids:
        owner_docs = await db.users.find(
            {"id": {"$in": owner_user_ids}},
            {"_id": 0, "id": 1, "name": 1},
        ).to_list(length=max(len(owner_user_ids), 1))
        owners_by_id = {str(owner.get("id")): str(owner.get("name") or "") for owner in owner_docs}

    items = [
        AdminVendorListItem(
            id=str(v.get("id") or ""),
            business_name=str(v.get("business_name") or ""),
            status=v.get("status"),
            category_id=v.get("category_id"),
            city=v.get("city"),
            created_at=v.get("created_at"),
            owner_name=owners_by_id.get(str(v.get("user_id")), None),
            verification_status=v.get("verification_status") or v.get("kyc_status"),
        )
        for v in docs
    ]
    data = PaginatedResponse[AdminVendorListItem](items=items, total=total, skip=skip, limit=limit)
    return ResponseEnvelope[PaginatedResponse[AdminVendorListItem]](
        success=True,
        data=data,
        message="Vendors fetched",
        request_id=_request_id(request),
    )


@router.get("/bookings", response_model=ResponseEnvelope[PaginatedResponse[AdminBookingListItem]])
async def list_bookings(
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    category_type: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> ResponseEnvelope[PaginatedResponse[AdminBookingListItem]]:
    db = get_db_from_request(request)
    query: dict[str, Any] = {}
    if status_filter:
        query["status"] = status_filter
    if category_type:
        query["category_type"] = category_type
    total = await db.bookings.count_documents(query)
    docs = await db.bookings.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    items = [
        AdminBookingListItem(
            id=str(b.get("id") or ""),
            status=b.get("status"),
            category_type=b.get("category_type"),
            user_id=b.get("user_id"),
            vendor_id=b.get("vendor_id"),
            total_amount_paise=int(
                b.get("total_amount_paise")
                or b.get("amount_gross_paise")
                or 0
            ),
            created_at=b.get("created_at"),
        )
        for b in docs
    ]
    data = PaginatedResponse[AdminBookingListItem](items=items, total=total, skip=skip, limit=limit)
    return ResponseEnvelope[PaginatedResponse[AdminBookingListItem]](
        success=True,
        data=data,
        message="Bookings fetched",
        request_id=_request_id(request),
    )


@router.post("/vendors/{vendor_id}/action", response_model=ResponseEnvelope[dict])
async def vendor_action(
    vendor_id: str,
    payload: VendorActionRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin),
):
    db = get_db_from_request(request)
    vendor = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")

    now = utcnow()
    update: dict[str, Any]
    if payload.action == "approve":
        update = {"status": "APPROVED", "is_active": True, "updated_at": now}
    elif payload.action == "reject":
        update = {"status": "REJECTED", "is_active": False, "updated_at": now}
    elif payload.action == "suspend":
        update = {"status": "SUSPENDED", "is_active": False, "updated_at": now}
    else:
        update = {"is_featured": True, "updated_at": now}

    result = await db.vendors.find_one_and_update(
        {"id": vendor_id},
        {"$set": update},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vendor update conflict")

    await _admin_audit_log(
        db=db,
        admin_id=str(current_user.get("id")),
        action=f"vendor_{payload.action}",
        target_type="vendor",
        target_id=vendor_id,
        request_id=_request_id(request),
        payload={"reason": payload.reason, "update": update},
    )
    return ResponseEnvelope[dict](
        success=True,
        data=result,
        message="Vendor action applied",
        request_id=_request_id(request),
    )


@router.patch("/vendors/{vendor_id}", response_model=ResponseEnvelope[dict])
async def admin_patch_vendor(
    vendor_id: str,
    payload: VendorAdminPatch,
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin),
):
    db = get_db_from_request(request)
    vendor = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")

    update = payload.model_dump(exclude_unset=True)
    if not update:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    update["updated_at"] = utcnow()

    updated = await db.vendors.find_one_and_update(
        {"id": vendor_id},
        {"$set": update},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vendor update conflict")

    await _admin_audit_log(
        db=db,
        admin_id=str(current_user.get("id")),
        action="vendor_admin_patch",
        target_type="vendor",
        target_id=vendor_id,
        request_id=_request_id(request),
        payload={"update": update},
    )
    return ResponseEnvelope[dict](
        success=True,
        data=updated,
        message="Vendor patched",
        request_id=_request_id(request),
    )


@router.put("/vendors/{vendor_id}", response_model=ResponseEnvelope[dict])
async def admin_patch_vendor_put(
    vendor_id: str,
    payload: VendorAdminPatch,
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin),
):
    return await admin_patch_vendor(vendor_id, payload, request, current_user)


@router.get("/users", response_model=ResponseEnvelope[PaginatedResponse[AdminUserListItem]])
async def list_users(
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin),
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_blocked: Optional[bool] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> ResponseEnvelope[PaginatedResponse[AdminUserListItem]]:
    db = get_db_from_request(request)
    query: dict[str, Any] = {}
    if role:
        query["role"] = role
    if is_active is not None:
        query["is_active"] = is_active
    if is_blocked is not None:
        query["is_blocked"] = is_blocked

    total = await db.users.count_documents(query)
    docs = await db.users.find(
        query,
        {"_id": 0, "password_hash": 0, "hashed_password": 0},
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    items = [
        AdminUserListItem(
            id=str(u.get("id") or ""),
            name=u.get("name"),
            email=u.get("email"),
            role=u.get("role"),
            is_active=bool(u.get("is_active", True)),
            is_blocked=bool(u.get("is_blocked", False)),
            created_at=u.get("created_at"),
        )
        for u in docs
    ]
    data = PaginatedResponse[AdminUserListItem](items=items, total=total, skip=skip, limit=limit)
    return ResponseEnvelope[PaginatedResponse[AdminUserListItem]](
        success=True,
        data=data,
        message="Users fetched",
        request_id=_request_id(request),
    )


@router.get("/payments", response_model=ResponseEnvelope[PaginatedResponse[AdminPaymentListItem]])
async def list_payments(
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=500),
) -> ResponseEnvelope[PaginatedResponse[AdminPaymentListItem]]:
    db = get_db_from_request(request)
    query: dict[str, Any] = {}
    if status_filter:
        query["status"] = status_filter
    total = await db.payments.count_documents(query)
    docs = await db.payments.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    items = [
        AdminPaymentListItem(
            id=str(p.get("id") or ""),
            status=p.get("status"),
            amount_paise=int(p.get("amount_paise") or p.get("amount") or 0),
            booking_intent_id=p.get("booking_intent_id"),
            user_id=p.get("user_id"),
            created_at=p.get("created_at"),
        )
        for p in docs
    ]
    data = PaginatedResponse[AdminPaymentListItem](items=items, total=total, skip=skip, limit=limit)
    return ResponseEnvelope[PaginatedResponse[AdminPaymentListItem]](
        success=True,
        data=data,
        message="Payments fetched",
        request_id=_request_id(request),
    )


@router.post("/payments/{payment_id}/refund", response_model=ResponseEnvelope[dict])
async def refund_payment(
    payment_id: str,
    payload: AdminRefundRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin),
):
    db = get_db_from_request(request)
    payment = await db.payments.find_one({"id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    now = utcnow()
    await db.payments.update_one(
        {"id": payment_id},
        {"$set": {"status": "REFUNDED", "refund_reason": payload.reason, "updated_at": now}},
    )
    refund_doc = {
        "id": f"ref_{uuid4().hex}",
        "payment_id": payment_id,
        "booking_id": payment.get("booking_id"),
        "amount_paise": int(payment.get("amount", 0) or 0),
        "status": "REQUESTED",
        "reason": payload.reason or "admin_refund",
        "requested_by": "admin",
        "created_at": now,
        "updated_at": now,
    }
    await db.refunds.insert_one(refund_doc)

    await _admin_audit_log(
        db=db,
        admin_id=str(current_user.get("id")),
        action="payment_refund_requested",
        target_type="payment",
        target_id=payment_id,
        request_id=_request_id(request),
        payload={"reason": payload.reason},
    )
    return ResponseEnvelope[dict](
        success=True,
        data={"payment_id": payment_id, "refund_id": refund_doc["id"]},
        message="Refund requested",
        request_id=_request_id(request),
    )


@router.post("/users/{user_id}/action", response_model=ResponseEnvelope[dict])
async def user_action(
    user_id: str,
    payload: UserActionRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin),
):
    db = get_db_from_request(request)
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    now = utcnow()
    if payload.action == "block":
        update = {"is_blocked": True, "is_active": False, "updated_at": now}
    else:
        update = {"is_blocked": False, "is_active": True, "updated_at": now}

    updated = await db.users.find_one_and_update(
        {"id": user_id},
        {"$set": update},
        projection={"_id": 0, "password_hash": 0, "hashed_password": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User update conflict")

    await _admin_audit_log(
        db=db,
        admin_id=str(current_user.get("id")),
        action=f"user_{payload.action}",
        target_type="user",
        target_id=user_id,
        request_id=_request_id(request),
        payload={"reason": payload.reason},
    )
    return ResponseEnvelope[dict](
        success=True,
        data=updated,
        message="User action applied",
        request_id=_request_id(request),
    )


@router.get("/payouts", response_model=ResponseEnvelope[PaginatedResponse[AdminPayoutListItem]])
async def list_payouts(
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin),
    status_filter: Optional[str] = Query(default=PayoutStatus.PENDING.value, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> ResponseEnvelope[PaginatedResponse[AdminPayoutListItem]]:
    db = get_db_from_request(request)
    query: dict[str, Any] = {}
    if status_filter:
        query["status"] = status_filter
    total = await db.payouts.count_documents(query)
    docs = await db.payouts.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    items = [
        AdminPayoutListItem(
            id=str(p.get("id") or ""),
            vendor_id=p.get("vendor_id"),
            amount=float(p.get("amount") or 0),
            status=p.get("status"),
            requested_at=p.get("requested_at") or p.get("created_at"),
            processed_at=p.get("processed_at") or p.get("approved_at"),
        )
        for p in docs
    ]
    data = PaginatedResponse[AdminPayoutListItem](items=items, total=total, skip=skip, limit=limit)
    return ResponseEnvelope[PaginatedResponse[AdminPayoutListItem]](
        success=True,
        data=data,
        message="Payouts fetched",
        request_id=_request_id(request),
    )


@router.post("/payouts/{payout_id}/action", response_model=ResponseEnvelope[dict])
async def payout_action(
    payout_id: str,
    payload: PayoutActionRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin),
    x_idempotency_key: str | None = Header(default=None, alias="x-idempotency-key"),
):
    db = get_db_from_request(request)
    admin_id = str(current_user.get("id"))

    if payload.action == "approve":
        if not x_idempotency_key:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing x-idempotency-key header")
        payout_service = PaymentExecutionService(db=db, razorpay_client=request.app.state.razorpay_client)
        updated = await payout_service.execute_vendor_payout(
            payout_id=payout_id,
            actor_id=admin_id,
            idempotency_key=x_idempotency_key,
        )
    else:
        updated = await db.payouts.find_one_and_update(
            {"id": payout_id, "status": PayoutStatus.PENDING.value},
            {
                "$set": {
                    "status": PayoutStatus.REJECTED.value,
                    "rejected_by": admin_id,
                    "rejected_at": utcnow(),
                    "updated_at": utcnow(),
                    "note": payload.reason or "Rejected by admin",
                }
            },
            projection={"_id": 0},
            return_document=ReturnDocument.AFTER,
        )
        if not updated:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payout not found or not pending")

    await _admin_audit_log(
        db=db,
        admin_id=admin_id,
        action=f"payout_{payload.action}",
        target_type="payout",
        target_id=payout_id,
        request_id=_request_id(request),
        payload={"reason": payload.reason},
    )
    return ResponseEnvelope[dict](
        success=True,
        data=updated,
        message="Payout action applied",
        request_id=_request_id(request),
    )


@router.get("/disputes", response_model=ResponseEnvelope[list[dict]])
async def list_disputes(
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
):
    db = get_db_from_request(request)
    query: dict[str, Any] = {}
    if status_filter:
        query["status"] = status_filter
    disputes = await db.disputes.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    return ResponseEnvelope[list[dict]](
        success=True,
        data=disputes,
        message="Disputes fetched",
        request_id=_request_id(request),
    )


@router.post("/disputes/{dispute_id}/resolve", response_model=ResponseEnvelope[dict])
async def resolve_dispute(
    dispute_id: str,
    payload: DisputeResolveRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin),
):
    db = get_db_from_request(request)
    now = utcnow()
    updated = await db.disputes.find_one_and_update(
        {"id": dispute_id},
        {
            "$set": {
                "status": "resolved",
                "outcome": payload.outcome,
                "resolution": payload.resolution,
                "resolved_by": str(current_user.get("id")),
                "resolved_at": now,
                "updated_at": now,
            }
        },
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found")

    await _admin_audit_log(
        db=db,
        admin_id=str(current_user.get("id")),
        action="dispute_resolved",
        target_type="dispute",
        target_id=dispute_id,
        request_id=_request_id(request),
        payload={"outcome": payload.outcome},
    )
    return ResponseEnvelope[dict](
        success=True,
        data=updated,
        message="Dispute resolved",
        request_id=_request_id(request),
    )


@router.get("/analytics/revenue", response_model=ResponseEnvelope[dict])
async def revenue_analytics(
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin),
):
    db = get_db_from_request(request)
    pipeline = [
        {
            "$group": {
                "_id": None,
                "gross_paise": {"$sum": {"$ifNull": ["$amount_gross_paise", 0]}},
                "commission_paise": {"$sum": {"$ifNull": ["$commission_amount_paise", 0]}},
                "vendor_net_paise": {"$sum": {"$ifNull": ["$vendor_net_paise", 0]}},
                "bookings_count": {"$sum": 1},
            }
        }
    ]
    agg = await db.bookings.aggregate(pipeline).to_list(length=1)
    summary = agg[0] if agg else {"gross_paise": 0, "commission_paise": 0, "vendor_net_paise": 0, "bookings_count": 0}
    return ResponseEnvelope[dict](
        success=True,
        data=summary,
        message="Revenue analytics fetched",
        request_id=_request_id(request),
    )


@router.get("/analytics/bookings", response_model=ResponseEnvelope[dict])
async def booking_analytics(
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin),
):
    db = get_db_from_request(request)
    status_pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    category_pipeline = [{"$group": {"_id": "$category_type", "count": {"$sum": 1}}}]
    status_counts = await db.bookings.aggregate(status_pipeline).to_list(length=50)
    category_counts = await db.bookings.aggregate(category_pipeline).to_list(length=20)

    data = {
        "by_status": {str(x.get("_id")): int(x.get("count", 0)) for x in status_counts},
        "by_category": {str(x.get("_id")): int(x.get("count", 0)) for x in category_counts},
    }
    return ResponseEnvelope[dict](
        success=True,
        data=data,
        message="Booking analytics fetched",
        request_id=_request_id(request),
    )


@router.get("/audit-logs", response_model=ResponseEnvelope[PaginatedResponse[AdminAuditLog]])
async def admin_audit_logs(
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin),
    admin_id: Optional[str] = None,
    action_type: Optional[str] = None,
    target_type: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> ResponseEnvelope[PaginatedResponse[AdminAuditLog]]:
    db = get_db_from_request(request)
    query: dict[str, Any] = {}
    if admin_id:
        query["admin_id"] = admin_id
    if action_type:
        query["action_type"] = action_type
    if target_type:
        query["target_type"] = target_type

    total = await db.admin_audit_logs.count_documents(query)
    docs = await db.admin_audit_logs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    items = [
        AdminAuditLog(
            id=str(log.get("id") or ""),
            admin_id=log.get("admin_id"),
            action_type=log.get("action_type"),
            target_type=log.get("target_type"),
            target_id=log.get("target_id"),
            metadata=dict(log.get("metadata") or log.get("payload") or {}),
            created_at=log.get("created_at"),
        )
        for log in docs
    ]
    data = PaginatedResponse[AdminAuditLog](items=items, total=total, skip=skip, limit=limit)
    return ResponseEnvelope[PaginatedResponse[AdminAuditLog]](
        success=True,
        data=data,
        message="Admin audit logs fetched",
        request_id=_request_id(request),
    )


@router.get("/incidents")
async def admin_incidents(
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin),
):
    _ = request
    return {"cancellations": [], "replacements": []}
