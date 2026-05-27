from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from canonical_models.common import utcnow
from shadiro_delivery_network.assignment_engine import partner_max_tier, rank_partners
from shadiro_delivery_network.constants import (
    COLLECTION_JOBS,
    COLLECTION_PARTNERS,
    DeliveryJobState,
    LogisticsTier,
    PartnerStatus,
    partner_can_carry_tier,
)
from shadiro_delivery_network.fraud_service import FraudDetectionService
from shadiro_delivery_network.notification_bridge import emit_delivery_event
from shadiro_delivery_network.qr_service import QRService
from shadiro_delivery_network.tracking_service import TrackingService

logger = logging.getLogger(__name__)

OFFER_TTL_SECONDS = 45


def _qr_secret(settings) -> str:
    raw = getattr(settings, "DELIVERY_QR_HMAC_SECRET", None) or ""
    if str(raw).strip():
        return str(raw).strip()
    return settings.JWT_SECRET_KEY


async def resolve_vendor_id_for_user(db: AsyncIOMotorDatabase, vendor_user_id: str) -> Optional[str]:
    doc = await db.vendors.find_one({"user_id": str(vendor_user_id)}, {"_id": 0, "id": 1})
    return str(doc["id"]) if doc and doc.get("id") else None


async def get_or_create_partner(db: AsyncIOMotorDatabase, user_id: str) -> dict[str, Any]:
    existing = await db[COLLECTION_PARTNERS].find_one({"user_id": str(user_id)}, {"_id": 0})
    if existing:
        return existing
    pid = f"dp_{uuid4().hex}"
    now = utcnow()
    doc = {
        "id": pid,
        "user_id": str(user_id),
        "vehicle_types": [],
        "capacity_kg": 15,
        "status": PartnerStatus.PENDING.value,
        "verification": {},
        "is_online": False,
        "last_lat": None,
        "last_lng": None,
        "last_location_at": None,
        "rating_avg": 4.5,
        "acceptance_rate": 0.9,
        "active_job_count": 0,
        "fraud_score": 0.0,
        "network_reliability": 0.95,
        "wallet_balance_paise": 0,
        "device_ids": [],
        "created_at": now,
        "updated_at": now,
    }
    await db[COLLECTION_PARTNERS].insert_one(doc)
    return doc


async def maybe_advance_offer(db: AsyncIOMotorDatabase, job: dict[str, Any], request: Optional[Request]) -> dict[str, Any]:
    now = utcnow()
    if job.get("state") != DeliveryJobState.ASSIGNED.value:
        return job
    q = job.get("assignment_queue") or []
    cursor = int(job.get("offer_cursor") or 0)
    active = job.get("active_offer_partner_id")
    exp = job.get("offer_expires_at")
    if not active or not q or cursor >= len(q):
        return job
    if exp and isinstance(exp, datetime) and exp > now:
        return job
    nxt = cursor + 1
    nxt_partner = q[nxt] if nxt < len(q) else None
    patch: dict[str, Any] = {
        "offer_cursor": nxt,
        "active_offer_partner_id": nxt_partner,
        "offer_expires_at": now + timedelta(seconds=OFFER_TTL_SECONDS) if nxt_partner else None,
        "updated_at": now,
    }
    if not nxt_partner:
        patch["last_assignment_note"] = "exhausted_partner_queue"
    updated = await db[COLLECTION_JOBS].find_one_and_update(
        {"id": job["id"]},
        {"$set": patch},
        return_document=ReturnDocument.AFTER,
    )
    if request and nxt_partner:
        pdoc = await db[COLLECTION_PARTNERS].find_one({"id": nxt_partner}, {"_id": 0, "user_id": 1})
        uid = str(pdoc.get("user_id")) if pdoc else ""
        await emit_delivery_event(
            request,
            event_type="delivery.offer",
            payload={"job_id": job["id"], "expires_at": patch["offer_expires_at"].isoformat()},
            notify_user_ids=[uid] if uid else [],
            job_id=job["id"],
        )
    return updated or job


async def run_assignment_for_job(db: AsyncIOMotorDatabase, job_id: str, request: Request) -> dict[str, Any]:
    job = await db[COLLECTION_JOBS].find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    tier = str(job.get("logistics_tier") or LogisticsTier.BIKE.value)
    weight = float(job.get("weight_kg") or 1)
    pickup = job.get("pickup") or {}
    plat = float(pickup.get("lat") or 19.076)
    plng = float(pickup.get("lng") or 72.8777)

    q: dict[str, Any] = {
        "status": PartnerStatus.VERIFIED.value,
        "is_online": True,
        "capacity_kg": {"$gte": weight},
    }
    cursor = db[COLLECTION_PARTNERS].find(q, {"_id": 0})
    partners = await cursor.to_list(length=200)
    eligible = []
    for p in partners:
        vt = p.get("vehicle_types") or []
        mx = partner_max_tier([str(x) for x in vt])
        if partner_can_carry_tier(mx, tier):
            eligible.append(p)

    ranked = rank_partners(eligible, pickup_lat=plat, pickup_lng=plng, limit=30)
    queue = [str(p["id"]) for p in ranked]
    now = utcnow()
    active = queue[0] if queue else None
    await db[COLLECTION_JOBS].update_one(
        {"id": job_id},
        {
            "$set": {
                "assignment_queue": queue,
                "offer_cursor": 0,
                "active_offer_partner_id": active,
                "offer_expires_at": now + timedelta(seconds=OFFER_TTL_SECONDS) if active else None,
                "updated_at": now,
            }
        },
    )
    if active:
        pdoc = await db[COLLECTION_PARTNERS].find_one({"id": active}, {"_id": 0, "user_id": 1})
        uid = str(pdoc.get("user_id")) if pdoc else ""
        await emit_delivery_event(
            request,
            event_type="delivery.offer",
            payload=_partner_offer_payload(job_id),
            notify_user_ids=[uid],
            job_id=job_id,
        )
    return await db[COLLECTION_JOBS].find_one({"id": job_id}, {"_id": 0}) or {}


def _partner_offer_payload(job_id: str) -> dict[str, Any]:
    return {"job_id": job_id, "hint": "fetch_inbox"}


async def create_delivery_job(
    db: AsyncIOMotorDatabase,
    request: Request,
    *,
    vendor_user_id: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    vendor_id = await resolve_vendor_id_for_user(db, vendor_user_id)
    if not vendor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vendor profile not found")
    now = utcnow()
    job_id = f"dj_{uuid4().hex}"
    pickup = body.get("pickup") or {}
    dropoff = body.get("dropoff") or {}
    job = {
        "id": job_id,
        "source_type": str(body.get("source_type") or "manual"),
        "source_order_id": str(body.get("source_order_id") or ""),
        "vendor_id": vendor_id,
        "vendor_user_id": str(vendor_user_id),
        "customer_user_id": str(body.get("customer_user_id") or ""),
        "pickup": pickup,
        "dropoff": dropoff,
        "weight_kg": float(body.get("weight_kg") or 1),
        "item_category": str(body.get("item_category") or "general"),
        "logistics_tier": str(body.get("logistics_tier") or LogisticsTier.BIKE.value),
        "heavy_tags": list(body.get("heavy_tags") or []),
        "state": DeliveryJobState.ASSIGNED.value,
        "details_unlocked": False,
        "pickup_confirmed_at": None,
        "accepted_partner_id": None,
        "assignment_queue": [],
        "offer_cursor": 0,
        "active_offer_partner_id": None,
        "offer_expires_at": None,
        "expected_earnings_paise": int(body.get("expected_earnings_paise") or 0),
        "eta_minutes": int(body.get("eta_minutes") or 35),
        "customer_contact_masked": str(body.get("customer_contact_masked") or "****"),
        "customer_contact_full": str(body.get("customer_contact_full") or ""),
        "distance_km_hint": float(body.get("distance_km_hint") or 0),
        "version": 1,
        "created_at": now,
        "updated_at": now,
    }
    await db[COLLECTION_JOBS].insert_one(job)
    await run_assignment_for_job(db, job_id, request)
    return await db[COLLECTION_JOBS].find_one({"id": job_id}, {"_id": 0}) or job


async def partner_inbox(db: AsyncIOMotorDatabase, partner_user_id: str, request: Request) -> list[dict[str, Any]]:
    p = await db[COLLECTION_PARTNERS].find_one({"user_id": str(partner_user_id)}, {"_id": 0})
    if not p:
        return []
    pid = str(p["id"])
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    async for job in db[COLLECTION_JOBS].find(
        {"active_offer_partner_id": pid, "state": DeliveryJobState.ASSIGNED.value},
        {"_id": 0},
    ):
        job = await maybe_advance_offer(db, job, request)
        if job.get("active_offer_partner_id") == pid and job["id"] not in seen:
            seen.add(job["id"])
            out.append(_public_offer(job))
    active = await db[COLLECTION_JOBS].find(
        {"accepted_partner_id": pid, "state": {"$ne": DeliveryJobState.DELIVERED.value}},
        {"_id": 0},
    ).to_list(length=20)
    for j in active:
        if j["id"] not in seen:
            seen.add(j["id"])
            out.append(_public_offer(j))
    return out


def _public_offer(job: dict[str, Any]) -> dict[str, Any]:
    locked = not bool(job.get("details_unlocked"))
    base: dict[str, Any] = {
        "job_id": job["id"],
        "pickup_label": (job.get("pickup") or {}).get("label") or "Pickup",
        "dropoff_label": (job.get("dropoff") or {}).get("label") or "Drop",
        "distance_km_hint": float(job.get("distance_km_hint") or 0),
        "weight_kg": job.get("weight_kg"),
        "item_category": job.get("item_category"),
        "expected_earnings_paise": job.get("expected_earnings_paise"),
        "eta_minutes": job.get("eta_minutes"),
        "state": job.get("state"),
        "offer_expires_at": job.get("offer_expires_at"),
    }
    if locked:
        base["details_locked"] = True
        base["customer_contact"] = job.get("customer_contact_masked")
    else:
        base["details_locked"] = False
        base["customer_contact"] = job.get("customer_contact_full") or job.get("customer_contact_masked")
        base["pickup"] = job.get("pickup")
        base["dropoff"] = job.get("dropoff")
    return base


async def accept_offer(db: AsyncIOMotorDatabase, request: Request, partner_user_id: str, job_id: str) -> dict[str, Any]:
    p = await db[COLLECTION_PARTNERS].find_one({"user_id": str(partner_user_id)}, {"_id": 0})
    if not p or p.get("status") != PartnerStatus.VERIFIED.value:
        raise HTTPException(status_code=403, detail="Partner not verified")
    pid = str(p["id"])
    now = utcnow()
    res = await db[COLLECTION_JOBS].find_one_and_update(
        {
            "id": job_id,
            "state": DeliveryJobState.ASSIGNED.value,
            "active_offer_partner_id": pid,
            "offer_expires_at": {"$gt": now},
        },
        {
            "$set": {
                "accepted_partner_id": pid,
                "state": DeliveryJobState.ACCEPTED.value,
                "updated_at": now,
            },
            "$inc": {"version": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not res:
        raise HTTPException(status_code=409, detail="Offer no longer valid")
    await db[COLLECTION_PARTNERS].update_one({"id": pid}, {"$inc": {"active_job_count": 1}})
    vu = str(res.get("vendor_user_id") or "")
    cu = str(res.get("customer_user_id") or "")
    await emit_delivery_event(
        request,
        event_type="delivery.accepted",
        payload={"job_id": job_id, "partner_id": pid},
        notify_user_ids=[x for x in (vu, cu) if x],
        job_id=job_id,
    )
    return res


async def reject_offer(db: AsyncIOMotorDatabase, request: Request, partner_user_id: str, job_id: str) -> dict[str, Any]:
    p = await db[COLLECTION_PARTNERS].find_one({"user_id": str(partner_user_id)}, {"_id": 0})
    if not p:
        raise HTTPException(status_code=404, detail="Partner profile not found")
    pid = str(p["id"])
    job = await db[COLLECTION_JOBS].find_one({"id": job_id}, {"_id": 0})
    if not job or job.get("active_offer_partner_id") != pid:
        raise HTTPException(status_code=409, detail="No active offer for this partner")
    now = utcnow()
    q = job.get("assignment_queue") or []
    cur = int(job.get("offer_cursor") or 0)
    nxt = cur + 1
    nxt_partner = q[nxt] if nxt < len(q) else None
    await db[COLLECTION_JOBS].update_one(
        {"id": job_id},
        {
            "$set": {
                "offer_cursor": nxt,
                "active_offer_partner_id": nxt_partner,
                "offer_expires_at": now + timedelta(seconds=OFFER_TTL_SECONDS) if nxt_partner else None,
                "updated_at": now,
            }
        },
    )
    if nxt_partner:
        pdoc = await db[COLLECTION_PARTNERS].find_one({"id": nxt_partner}, {"_id": 0, "user_id": 1})
        uid = str(pdoc.get("user_id")) if pdoc else ""
        await emit_delivery_event(
            request,
            event_type="delivery.offer",
            payload={"job_id": job_id},
            notify_user_ids=[uid] if uid else [],
            job_id=job_id,
        )
    return await db[COLLECTION_JOBS].find_one({"id": job_id}, {"_id": 0}) or {}


async def scan_pickup_qr(
    db: AsyncIOMotorDatabase,
    request: Request,
    settings,
    partner_user_id: str,
    job_id: str,
    *,
    payload_b64: str,
    scan_lat: Optional[float],
    scan_lng: Optional[float],
    client_ts: Optional[int],
    device_id: Optional[str],
) -> dict[str, Any]:
    p = await db[COLLECTION_PARTNERS].find_one({"user_id": str(partner_user_id)}, {"_id": 0})
    if not p:
        raise HTTPException(status_code=404, detail="Partner not found")
    pid = str(p["id"])
    job = await db[COLLECTION_JOBS].find_one({"id": job_id}, {"_id": 0})
    if not job or str(job.get("accepted_partner_id")) != pid:
        raise HTTPException(status_code=403, detail="Not assigned partner on this job")

    qr = QRService(db, _qr_secret(settings))
    fraud = FraudDetectionService(db)
    try:
        envelope = qr.decode_payload_b64(payload_b64)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid QR payload") from exc

    vendor_id = str(job.get("vendor_id") or "")
    pickup = job.get("pickup") or {}
    vlat = pickup.get("lat")
    vlng = pickup.get("lng")
    server_ts = int(datetime.now(timezone.utc).timestamp())
    ok_ctx, _ = await fraud.evaluate_qr_scan_context(
        job_id=job_id,
        partner_id=pid,
        vendor_lat=float(vlat) if vlat is not None else None,
        vendor_lng=float(vlng) if vlng is not None else None,
        scan_lat=scan_lat,
        scan_lng=scan_lng,
        client_ts=client_ts,
        server_ts=server_ts,
        device_id=device_id,
    )
    if not ok_ctx:
        raise HTTPException(status_code=403, detail="Security checks failed")

    ok, reason, _ = await qr.consume_if_valid(envelope=envelope, expected_partner_id=pid)
    if not ok:
        await fraud.log(
            event_type="qr_consume_failed",
            severity="medium",
            job_id=job_id,
            partner_id=pid,
            vendor_id=vendor_id,
            details={"reason": reason},
            device_id=device_id,
        )
        raise HTTPException(status_code=400, detail=f"QR invalid: {reason}")

    now = utcnow()
    await db[COLLECTION_JOBS].update_one(
        {"id": job_id},
        {
            "$set": {
                "details_unlocked": True,
                "pickup_confirmed_at": now,
                "state": DeliveryJobState.PICKED_UP.value,
                "updated_at": now,
            }
        },
    )
    await fraud.log(
        event_type="qr_pickup_success",
        severity="low",
        job_id=job_id,
        partner_id=pid,
        vendor_id=vendor_id,
        details={"device_id": device_id},
        device_id=device_id,
    )
    vu = str(job.get("vendor_user_id") or "")
    cu = str(job.get("customer_user_id") or "")
    await emit_delivery_event(
        request,
        event_type="delivery.picked_up",
        payload={"job_id": job_id},
        notify_user_ids=[x for x in (vu, cu, str(partner_user_id)) if x],
        job_id=job_id,
    )
    if device_id:
        await db[COLLECTION_PARTNERS].update_one(
            {"id": pid},
            {"$addToSet": {"device_ids": str(device_id)}},
        )
    return await db[COLLECTION_JOBS].find_one({"id": job_id}, {"_id": 0}) or {}


async def issue_vendor_qr(db: AsyncIOMotorDatabase, settings, vendor_user_id: str, job_id: str) -> dict[str, Any]:
    vendor_id = await resolve_vendor_id_for_user(db, vendor_user_id)
    if not vendor_id:
        raise HTTPException(status_code=403, detail="Vendor not found")
    job = await db[COLLECTION_JOBS].find_one({"id": job_id, "vendor_id": vendor_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    partner_id = str(job.get("accepted_partner_id") or "")
    if not partner_id:
        raise HTTPException(status_code=400, detail="Assign a partner before issuing pickup QR")
    qr = QRService(db, _qr_secret(settings))
    res = await qr.issue_vendor_pickup_qr(job_id=job_id, vendor_id=str(vendor_id), partner_id=partner_id)
    return {"payload_b64": res.payload_b64, "expires_at": res.expires_at.isoformat(), "jti": res.jti}


def _partner_may_transition(cur: str, nxt: str, job: dict[str, Any]) -> bool:
    if nxt == DeliveryJobState.FAILED.value:
        return cur != DeliveryJobState.DELIVERED.value
    if nxt == DeliveryJobState.PICKED_UP.value:
        return False
    pairs = {
        (DeliveryJobState.ACCEPTED.value, DeliveryJobState.ARRIVING_VENDOR.value),
        (DeliveryJobState.PICKED_UP.value, DeliveryJobState.IN_TRANSIT.value),
        (DeliveryJobState.IN_TRANSIT.value, DeliveryJobState.ARRIVING_CUSTOMER.value),
        (DeliveryJobState.ARRIVING_CUSTOMER.value, DeliveryJobState.DELIVERED.value),
    }
    return (cur, nxt) in pairs


async def transition_job_state(
    db: AsyncIOMotorDatabase,
    request: Request,
    partner_user_id: str,
    job_id: str,
    new_state: str,
) -> dict[str, Any]:
    p = await db[COLLECTION_PARTNERS].find_one({"user_id": str(partner_user_id)}, {"_id": 0})
    if not p:
        raise HTTPException(status_code=404, detail="Partner not found")
    pid = str(p["id"])
    job = await db[COLLECTION_JOBS].find_one({"id": job_id, "accepted_partner_id": pid}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    cur = str(job.get("state") or "")
    if not _partner_may_transition(cur, new_state, job):
        raise HTTPException(status_code=400, detail="Invalid state transition")
    if new_state == DeliveryJobState.IN_TRANSIT.value and not job.get("details_unlocked"):
        raise HTTPException(status_code=400, detail="Pickup QR required before in_transit")
    now = utcnow()
    await db[COLLECTION_JOBS].update_one({"id": job_id}, {"$set": {"state": new_state, "updated_at": now}})
    j = await db[COLLECTION_JOBS].find_one({"id": job_id}, {"_id": 0})
    vu = str(j.get("vendor_user_id") or "") if j else ""
    cu = str(j.get("customer_user_id") or "") if j else ""
    await emit_delivery_event(
        request,
        event_type="delivery.state",
        payload={"job_id": job_id, "state": new_state},
        notify_user_ids=[x for x in (vu, cu, str(partner_user_id)) if x],
        job_id=job_id,
    )
    if new_state == DeliveryJobState.DELIVERED.value and j:
        await db[COLLECTION_PARTNERS].update_one(
            {"id": pid},
            {"$inc": {"active_job_count": -1, "completed_deliveries": 1}},
        )
    return j or {}


async def post_tracking(
    db: AsyncIOMotorDatabase,
    request: Request,
    partner_user_id: str,
    job_id: str,
    *,
    lat: float,
    lng: float,
    accuracy_m: Optional[float] = None,
) -> dict[str, Any]:
    p = await db[COLLECTION_PARTNERS].find_one({"user_id": str(partner_user_id)}, {"_id": 0})
    if not p:
        raise HTTPException(status_code=404, detail="Partner not found")
    pid = str(p["id"])
    job = await db[COLLECTION_JOBS].find_one({"id": job_id, "accepted_partner_id": pid}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    tr = TrackingService(db)
    tid = await tr.append_location(job_id=job_id, partner_id=pid, lat=lat, lng=lng, accuracy_m=accuracy_m)
    hub = getattr(request.app.state, "delivery_hub", None)
    if hub is not None:
        await hub.publish_to_job(
            job_id,
            {
                "type": "delivery.location",
                "job_id": job_id,
                "payload": {"lat": lat, "lng": lng, "tracking_point_id": tid},
                "ts": datetime.now(timezone.utc).isoformat(),
            },
        )
    return {"ok": True, "tracking_point_id": tid}
