from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pymongo import ReturnDocument
from pydantic import BaseModel, ConfigDict, Field

from canonical_models.common import ResponseEnvelope, utcnow
from core.config import get_settings
from core.database import get_db_from_request
from core.security import get_current_user, require_admin_canonical, require_vendor_canonical
from shadiro_delivery_network.constants import (
    COLLECTION_JOBS,
    COLLECTION_PARTNERS,
    PartnerStatus,
    VerificationDocType,
)
from shadiro_delivery_network.delivery_service import (
    accept_offer,
    create_delivery_job,
    get_or_create_partner,
    issue_vendor_qr,
    partner_inbox,
    post_tracking,
    reject_offer,
    resolve_vendor_id_for_user,
    scan_pickup_qr,
    transition_job_state,
)

router = APIRouter(prefix="/api/delivery-network", tags=["Shadiro Delivery Network"])
settings = get_settings()


def _rid(request: Request) -> str:
    return str(getattr(request.state, "request_id", "") or "")


class PartnerRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vehicle_types: list[str] = Field(min_length=1, max_length=8)
    capacity_kg: float = Field(ge=1, le=50_000)


class PartnerOnlineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_online: bool


class PartnerLocationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class VerificationPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    doc_type: VerificationDocType
    payload: dict[str, Any] = Field(default_factory=dict)


class VendorCreateJobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_type: str = "manual"
    source_order_id: str = ""
    customer_user_id: str = ""
    pickup: dict[str, Any]
    dropoff: dict[str, Any]
    weight_kg: float = Field(ge=0.1, le=50_000)
    item_category: str = "general"
    logistics_tier: str = "bike"
    heavy_tags: list[str] = Field(default_factory=list)
    expected_earnings_paise: int = 0
    eta_minutes: int = 35
    customer_contact_masked: str = "****"
    customer_contact_full: str = ""
    distance_km_hint: float = 0


class ScanQrRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    payload_b64: str = Field(min_length=8)
    scan_lat: Optional[float] = None
    scan_lng: Optional[float] = None
    client_ts: Optional[int] = None
    device_id: Optional[str] = None


class TransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state: str


class TrackingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lat: float
    lng: float
    accuracy_m: Optional[float] = None


class AdminPartnerStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: PartnerStatus
    note: str = ""


@router.post("/partner/register", response_model=ResponseEnvelope[dict])
async def partner_register(
    request: Request,
    body: PartnerRegisterRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_from_request),
):
    p = await get_or_create_partner(db, str(current_user["id"]))
    now = utcnow()
    await db[COLLECTION_PARTNERS].update_one(
        {"id": p["id"]},
        {
            "$set": {
                "vehicle_types": body.vehicle_types,
                "capacity_kg": body.capacity_kg,
                "updated_at": now,
            }
        },
    )
    doc = await db[COLLECTION_PARTNERS].find_one({"id": p["id"]}, {"_id": 0})
    return ResponseEnvelope[dict](success=True, data=doc or {}, message="", request_id=_rid(request))


@router.get("/partner/me", response_model=ResponseEnvelope[dict])
async def partner_me(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_from_request),
):
    p = await get_or_create_partner(db, str(current_user["id"]))
    return ResponseEnvelope[dict](success=True, data=p, message="", request_id=_rid(request))


@router.patch("/partner/online", response_model=ResponseEnvelope[dict])
async def partner_online(
    request: Request,
    body: PartnerOnlineRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_from_request),
):
    p = await get_or_create_partner(db, str(current_user["id"]))
    await db[COLLECTION_PARTNERS].update_one(
        {"id": p["id"]},
        {"$set": {"is_online": body.is_online, "updated_at": utcnow()}},
    )
    doc = await db[COLLECTION_PARTNERS].find_one({"id": p["id"]}, {"_id": 0})
    return ResponseEnvelope[dict](success=True, data=doc or {}, message="", request_id=_rid(request))


@router.patch("/partner/location", response_model=ResponseEnvelope[dict])
async def partner_location(
    request: Request,
    body: PartnerLocationRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_from_request),
):
    p = await get_or_create_partner(db, str(current_user["id"]))
    now = utcnow()
    await db[COLLECTION_PARTNERS].update_one(
        {"id": p["id"]},
        {"$set": {"last_lat": body.lat, "last_lng": body.lng, "last_location_at": now, "updated_at": now}},
    )
    doc = await db[COLLECTION_PARTNERS].find_one({"id": p["id"]}, {"_id": 0})
    return ResponseEnvelope[dict](success=True, data=doc or {}, message="", request_id=_rid(request))


@router.patch("/partner/verification", response_model=ResponseEnvelope[dict])
async def partner_verification(
    request: Request,
    body: VerificationPatchRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_from_request),
):
    p = await get_or_create_partner(db, str(current_user["id"]))
    key = f"verification.{body.doc_type.value}"
    await db[COLLECTION_PARTNERS].update_one(
        {"id": p["id"]},
        {"$set": {key: body.payload, "updated_at": utcnow()}},
    )
    doc = await db[COLLECTION_PARTNERS].find_one({"id": p["id"]}, {"_id": 0})
    return ResponseEnvelope[dict](success=True, data=doc or {}, message="", request_id=_rid(request))


@router.get("/partner/inbox", response_model=ResponseEnvelope[list[dict]])
async def partner_inbox_route(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_from_request),
):
    rows = await partner_inbox(db, str(current_user["id"]), request)
    return ResponseEnvelope[list[dict]](success=True, data=rows, message="", request_id=_rid(request))


@router.post("/partner/jobs/{job_id}/accept", response_model=ResponseEnvelope[dict])
async def partner_accept(
    request: Request,
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_from_request),
):
    doc = await accept_offer(db, request, str(current_user["id"]), job_id)
    return ResponseEnvelope[dict](success=True, data=doc, message="", request_id=_rid(request))


@router.post("/partner/jobs/{job_id}/reject", response_model=ResponseEnvelope[dict])
async def partner_reject(
    request: Request,
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_from_request),
):
    doc = await reject_offer(db, request, str(current_user["id"]), job_id)
    return ResponseEnvelope[dict](success=True, data=doc, message="", request_id=_rid(request))


@router.post("/partner/jobs/{job_id}/scan-qr", response_model=ResponseEnvelope[dict])
async def partner_scan_qr(
    request: Request,
    job_id: str,
    body: ScanQrRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_from_request),
):
    doc = await scan_pickup_qr(
        db,
        request,
        settings,
        str(current_user["id"]),
        job_id,
        payload_b64=body.payload_b64,
        scan_lat=body.scan_lat,
        scan_lng=body.scan_lng,
        client_ts=body.client_ts,
        device_id=body.device_id,
    )
    return ResponseEnvelope[dict](success=True, data=doc, message="", request_id=_rid(request))


@router.post("/partner/jobs/{job_id}/transition", response_model=ResponseEnvelope[dict])
async def partner_transition(
    request: Request,
    job_id: str,
    body: TransitionRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_from_request),
):
    doc = await transition_job_state(db, request, str(current_user["id"]), job_id, body.state)
    return ResponseEnvelope[dict](success=True, data=doc, message="", request_id=_rid(request))


@router.post("/partner/jobs/{job_id}/track", response_model=ResponseEnvelope[dict])
async def partner_track(
    request: Request,
    job_id: str,
    body: TrackingRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_from_request),
):
    doc = await post_tracking(
        db,
        request,
        str(current_user["id"]),
        job_id,
        lat=body.lat,
        lng=body.lng,
        accuracy_m=body.accuracy_m,
    )
    return ResponseEnvelope[dict](success=True, data=doc, message="", request_id=_rid(request))


@router.post("/vendor/jobs", response_model=ResponseEnvelope[dict])
async def vendor_create_job(
    request: Request,
    body: VendorCreateJobRequest,
    current_user: dict = Depends(require_vendor_canonical),
    db=Depends(get_db_from_request),
):
    doc = await create_delivery_job(
        db,
        request,
        vendor_user_id=str(current_user["id"]),
        body=body.model_dump(),
    )
    return ResponseEnvelope[dict](success=True, data=doc, message="", request_id=_rid(request))


@router.get("/vendor/jobs", response_model=ResponseEnvelope[list[dict]])
async def vendor_list_jobs(
    request: Request,
    current_user: dict = Depends(require_vendor_canonical),
    db=Depends(get_db_from_request),
):
    vendor_id = await resolve_vendor_id_for_user(db, str(current_user["id"]))
    if not vendor_id:
        raise HTTPException(status_code=403, detail="Vendor not found")
    cur = db[COLLECTION_JOBS].find({"vendor_id": vendor_id}, {"_id": 0}).sort("created_at", -1).limit(100)
    rows = await cur.to_list(length=100)
    return ResponseEnvelope[list[dict]](success=True, data=rows, message="", request_id=_rid(request))


@router.post("/vendor/jobs/{job_id}/qr", response_model=ResponseEnvelope[dict])
async def vendor_issue_qr(
    request: Request,
    job_id: str,
    current_user: dict = Depends(require_vendor_canonical),
    db=Depends(get_db_from_request),
):
    doc = await issue_vendor_qr(db, settings, str(current_user["id"]), job_id)
    return ResponseEnvelope[dict](success=True, data=doc, message="", request_id=_rid(request))


@router.get("/admin/partners/pending", response_model=ResponseEnvelope[list[dict]])
async def admin_pending_partners(
    request: Request,
    current_user: dict = Depends(require_admin_canonical),
    db=Depends(get_db_from_request),
):
    cur = db[COLLECTION_PARTNERS].find({"status": PartnerStatus.PENDING.value}, {"_id": 0}).limit(200)
    rows = await cur.to_list(length=200)
    return ResponseEnvelope[list[dict]](success=True, data=rows, message="", request_id=_rid(request))


@router.post("/admin/partners/{partner_id}/status", response_model=ResponseEnvelope[dict])
async def admin_partner_status(
    request: Request,
    partner_id: str,
    body: AdminPartnerStatusRequest,
    current_user: dict = Depends(require_admin_canonical),
    db=Depends(get_db_from_request),
):
    res = await db[COLLECTION_PARTNERS].find_one_and_update(
        {"id": partner_id},
        {
            "$set": {
                "status": body.status.value,
                "admin_note": body.note,
                "updated_at": utcnow(),
            }
        },
        return_document=ReturnDocument.AFTER,
        projection={"_id": 0},
    )
    if not res:
        raise HTTPException(status_code=404, detail="Partner not found")
    return ResponseEnvelope[dict](success=True, data=res, message="", request_id=_rid(request))
