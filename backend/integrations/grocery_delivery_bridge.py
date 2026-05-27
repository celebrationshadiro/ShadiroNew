"""
Optional bridge from paid grocery bookings → Smart Delivery Network jobs.

Keeps grocery/payment code decoupled: only calls public delivery_service APIs.
Never raises into payment flows — failures are logged and swallowed.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from canonical_models.common import CategoryType, utcnow
from shadiro_delivery_network.constants import COLLECTION_JOBS, LogisticsTier
from shadiro_delivery_network.delivery_service import create_delivery_job

logger = logging.getLogger(__name__)

# Default map pins when vendor/customer geo is unknown (Mumbai centroid — replace with geocoding later).
_DEFAULT_LAT, _DEFAULT_LNG = 19.0760, 72.8777


class _AppStateShim:
    __slots__ = ("state",)

    def __init__(self, state: Any) -> None:
        self.state = state


class AppStateRequestShim:
    """Minimal object exposing ``request.app.state`` for delivery_service notifications."""

    __slots__ = ("app",)

    def __init__(self, app_state: Any) -> None:
        self.app = _AppStateShim(app_state)


def _estimate_weight_kg(booking: dict[str, Any]) -> float:
    total = 0.0
    for it in booking.get("items") or []:
        qty = float(it.get("qty", 1) or 1)
        meta = it.get("meta") or {}
        each = float(meta.get("weight_kg_each") or meta.get("weight_kg") or 0.5)
        total += qty * each
    return max(1.0, min(total, 50_000.0))


def _tier_for_weight(weight_kg: float) -> str:
    if weight_kg <= 15:
        return LogisticsTier.BIKE.value
    if weight_kg <= 80:
        return LogisticsTier.CAR.value
    if weight_kg <= 400:
        return LogisticsTier.TEMPO.value
    if weight_kg <= 1500:
        return LogisticsTier.MINI_TRUCK.value
    return LogisticsTier.HEAVY.value


async def try_spawn_grocery_delivery_after_paid_booking(
    *,
    db,
    app_state: Any,
    booking: dict[str, Any],
    intent: dict[str, Any],
    settings: Any,
) -> Optional[str]:
    """
    After Razorpay success materializes a grocery ``booking``, create a delivery job once.

    Returns delivery job id if created or already present, else None.
    """
    if not getattr(settings, "GROCERY_DELIVERY_AUTO_ENABLED", True):
        return None
    if app_state is None:
        return None

    if str(booking.get("category_type") or "").lower() != CategoryType.GROCERY.value:
        return None

    booking_id = str(booking.get("id") or "")
    if not booking_id:
        return None

    existing = await db[COLLECTION_JOBS].find_one(
        {"source_type": "grocery_order", "source_order_id": booking_id},
        {"_id": 0, "id": 1},
    )
    if existing:
        return str(existing["id"])

    vendor = await db.vendors.find_one(
        {"id": booking.get("vendor_id")},
        {"_id": 0, "user_id": 1, "business_name": 1, "city": 1, "location": 1},
    )
    if not vendor or not vendor.get("user_id"):
        logger.warning("grocery_delivery_skip_no_vendor_user", extra={"booking_id": booking_id})
        return None

    vendor_user_id = str(vendor["user_id"])
    meta = intent.get("meta") or booking.get("meta") or {}
    delivery_address = str(meta.get("delivery_address") or "Customer address on file").strip()
    weight_kg = _estimate_weight_kg(booking)
    tier = _tier_for_weight(weight_kg)

    city = str(vendor.get("city") or vendor.get("location") or "").strip()
    pickup_label = f"{vendor.get('business_name') or 'Vendor'}" + (f" · {city}" if city else "")

    body: dict[str, Any] = {
        "source_type": "grocery_order",
        "source_order_id": booking_id,
        "customer_user_id": str(booking.get("user_id") or ""),
        "pickup": {
            "lat": _DEFAULT_LAT,
            "lng": _DEFAULT_LNG,
            "label": pickup_label,
            "address": pickup_label,
        },
        "dropoff": {
            "lat": _DEFAULT_LAT + 0.02,
            "lng": _DEFAULT_LNG + 0.02,
            "label": "Delivery",
            "address": delivery_address[:500],
        },
        "weight_kg": weight_kg,
        "item_category": "grocery",
        "logistics_tier": tier,
        "heavy_tags": [],
        "expected_earnings_paise": int(getattr(settings, "GROCERY_DELIVERY_DEFAULT_EARNING_PAISE", 12_000)),
        "eta_minutes": int(getattr(settings, "GROCERY_DELIVERY_DEFAULT_ETA_MINUTES", 40)),
        "customer_contact_masked": "****",
        "customer_contact_full": "",
        "distance_km_hint": float(getattr(settings, "GROCERY_DELIVERY_DISTANCE_HINT_KM", 5.0)),
    }

    try:
        req = AppStateRequestShim(app_state)
        job = await create_delivery_job(db, req, vendor_user_id=vendor_user_id, body=body)
        job_id = str(job.get("id") or "")
        now = utcnow()
        await db.bookings.update_one(
            {"id": booking_id},
            {"$set": {"meta.delivery_job_id": job_id, "meta.delivery_spawned_at": now, "updated_at": now}},
        )
        logger.info(
            "grocery_delivery_job_spawned",
            extra={"event": "grocery_delivery_job_spawned", "booking_id": booking_id, "delivery_job_id": job_id},
        )
        return job_id or None
    except Exception:
        logger.exception("grocery_delivery_job_spawn_failed", extra={"booking_id": booking_id})
        return None
