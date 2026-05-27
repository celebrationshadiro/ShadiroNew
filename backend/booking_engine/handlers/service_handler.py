from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict

from fastapi import HTTPException

from booking_engine.category_config import SERVICE_CATEGORIES, normalize_category_slug
from booking_engine.lock_service import acquire_slot_lock, release_lock, utcnow
from booking_engine.handlers.base_handler import BaseBookingHandler
from booking_engine.models.booking_models import CategoryType


SERVICE_CATEGORY_META_FIELDS: dict[str, set[str]] = {
    "photography": {"shoot_type", "hours_required"},
    "catering": {"menu_type", "meals_count", "cuisine_type"},
    "decoration": {"theme", "venue_size_sqft", "decoration_type"},
    "makeup": {"service_type", "artists_count"},
    "lighting": {"lighting_type", "setup_hours", "equipment_list"},
    "videography": {"video_type", "hours_required", "drone_required"},
}


class ServiceBookingHandler(BaseBookingHandler):
    category_type = CategoryType.SERVICE

    @staticmethod
    def _extract_category_slug(payload: Dict[str, Any]) -> str:
        raw = (
            payload.get("category_slug")
            or payload.get("service_category")
            or payload.get("subcategory")
            or ""
        )
        return normalize_category_slug(str(raw))

    @staticmethod
    def _validate_category_meta(category_slug: str, category_meta: Dict[str, Any]) -> None:
        required_fields = SERVICE_CATEGORY_META_FIELDS.get(category_slug)
        if not required_fields:
            return
        missing = [field for field in required_fields if field not in category_meta or category_meta.get(field) in (None, "")]
        if missing:
            raise HTTPException(
                status_code=422,
                detail=f"Missing category_meta fields for {category_slug}: {', '.join(sorted(missing))}",
            )

    @staticmethod
    def vendor_response_deadline() -> Any:
        return utcnow() + timedelta(hours=4)

    async def validate_create(self, payload: Dict[str, Any], current_user: Dict[str, Any]) -> None:
        _ = current_user
        vendor = await self.db.vendors.find_one(
            {"id": payload["vendor_id"], "is_active": True},
            {"_id": 0, "id": 1},
        )
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not available")
        for key in ("event_date", "start_time", "end_time", "event_city", "event_location"):
            if not payload.get(key):
                raise HTTPException(status_code=422, detail=f"{key} is required")
        if float(payload.get("token_amount") or 0) <= 0:
            raise HTTPException(status_code=422, detail="token_amount must be greater than zero")

        category_slug = self._extract_category_slug(payload)
        if category_slug:
            if category_slug not in SERVICE_CATEGORIES:
                raise HTTPException(status_code=422, detail=f"Unsupported service category_slug: {category_slug}")
            self._validate_category_meta(category_slug, payload.get("category_meta") or {})

    async def reserve_resources(self, payload: Dict[str, Any], intent_id: str, ttl_seconds: int) -> Dict[str, Any]:
        _ = ttl_seconds
        lock_result = await acquire_slot_lock(
            self.db,
            vendor_id=payload["vendor_id"],
            date_value=payload["event_date"],
            intent_id=intent_id,
            ttl_min=30,
            start_time=payload["start_time"],
            end_time=payload["end_time"],
        )
        return {
            "type": "service_slot",
            "lock_id": lock_result["lock_id"],
            "expires_at": lock_result["expires_at"],
            "vendor_response_deadline": self.vendor_response_deadline(),
        }

    async def release_resources(self, reservation: Dict[str, Any]) -> None:
        lock_id = str(reservation.get("lock_id") or "")
        if lock_id:
            await release_lock(self.db, lock_id)

    def requires_vendor_acceptance(self) -> bool:
        return True

    def uses_escrow(self) -> bool:
        return True

    def payment_summary(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        token_amount = round(float(payload["token_amount"]), 2)
        return {
            "currency": "INR",
            "payable_now": token_amount,
            "token_amount": token_amount,
            "total_amount": token_amount,
            "settlement_mode": "escrow",
        }
