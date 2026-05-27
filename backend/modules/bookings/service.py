from __future__ import annotations

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from models import Booking, BookingContext, BookingItem, BookingStatus, UserRole, VendorType
from services.category_booking_flow import (
    build_payment_plan,
    CategoryBookingValidationError,
    get_booking_flow_template,
    normalize_category_id,
    validate_and_normalize_booking_details,
)
from services.vendor_type import resolve_vendor_type

from .repository import BookingRepository

logger = logging.getLogger(__name__)


class BookingService:
    def __init__(self, repo: BookingRepository):
        self.repo = repo

    async def get_booking_for_user(self, booking_id: str, current_user: Dict[str, Any]) -> Dict[str, Any]:
        booking = await self.repo.get_booking(booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        role = current_user.get("role")
        user_id = current_user.get("sub")

        if role == UserRole.ADMIN:
            return booking

        if role == UserRole.CUSTOMER and booking.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Not allowed")

        if role == UserRole.VENDOR:
            vendor_doc = await self.repo.get_vendor_by_user(user_id)
            if not vendor_doc or vendor_doc.get("id") != booking.get("vendor_id"):
                raise HTTPException(status_code=403, detail="Not allowed")

        return booking

    async def list_bookings_for_user(
        self,
        current_user: Dict[str, Any],
        skip: int,
        limit: int,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        role = current_user.get("role")
        user_id = current_user.get("sub")

        query: Dict[str, Any] = {}
        if status:
            query["status"] = status

        if role == UserRole.CUSTOMER:
            query["user_id"] = user_id
        elif role == UserRole.VENDOR:
            vendor_doc = await self.repo.get_vendor_by_user(user_id)
            if not vendor_doc:
                return []
            query["vendor_id"] = vendor_doc.get("id")

        return await self.repo.list_bookings(query, skip, limit)

    def _resolve_context(self, booking: Booking, vendor_doc: Optional[dict]) -> BookingContext:
        explicit = (booking.booking_context or "").upper() if booking.booking_context else None
        if explicit == BookingContext.GROCERY.value:
            raise HTTPException(status_code=400, detail="Use grocery checkout for delivery orders")
        if explicit == BookingContext.SERVICE.value:
            return BookingContext.SERVICE
        if vendor_doc:
            resolved = resolve_vendor_type(vendor_doc.get("category_id"), vendor_doc.get("vendor_type"))
            if resolved == VendorType.PRODUCT_VENDOR:
                raise HTTPException(status_code=400, detail="Grocery vendors do not accept bookings")
        return BookingContext.SERVICE

    def _validate_service_address(self, booking: Booking, event_doc: Optional[dict]):
        missing = []
        if not booking.event_date:
            missing.append("event_date")
        address_payload = (
            booking.event_address.model_dump()
            if hasattr(booking.event_address, "model_dump")
            else (booking.event_address or {})
        )
        location_fallback = booking.location or (event_doc.get("location") if event_doc else None)
        city_fallback = booking.event_city or (event_doc.get("city") if event_doc else None)
        if not address_payload and not location_fallback:
            missing.append("event_location")
        if not city_fallback and not address_payload.get("city"):
            missing.append("event_city")
        if missing:
            raise HTTPException(
                status_code=400, detail=f"Service booking missing required fields: {', '.join(missing)}"
            )
        if address_payload:
            address_payload.setdefault("address_type", "event")
            if address_payload.get("address_type") != "event":
                raise HTTPException(status_code=400, detail="Use event address for service bookings")
            if booking.event_address:
                booking.event_address = booking.event_address.__class__(**address_payload)
            else:
                booking.event_address = address_payload
        booking.ai_context_address = address_payload or {
            "address_type": "event",
            "location": location_fallback,
            "city": city_fallback,
        }

    async def create_booking(self, booking: Booking, current_user: Dict[str, Any]) -> Dict[str, Any]:
        vendor_doc = None
        if booking.vendor_id:
            vendor_doc = await self.repo.get_vendor(booking.vendor_id)
            if not vendor_doc:
                raise HTTPException(status_code=404, detail="Vendor not found")
        context = self._resolve_context(booking, vendor_doc)
        booking.booking_context = context

        if booking.delivery_address:
            raise HTTPException(status_code=400, detail="Service bookings cannot include delivery_address")

        event_doc = None
        if booking.event_id:
            event_doc = await self.repo.get_event(booking.event_id)
            if not event_doc:
                raise HTTPException(status_code=404, detail="Event not found")
            if event_doc.get("user_id") and event_doc.get("user_id") != current_user.get("sub"):
                raise HTTPException(status_code=403, detail="Event does not belong to user")
            booking.event_date = booking.event_date or event_doc.get("date")
            booking.event_city = booking.event_city or event_doc.get("city") or event_doc.get("location")
            booking.location = booking.location or event_doc.get("location")

        if vendor_doc and booking.event_city:
            vendor_city = (vendor_doc.get("city") or "").lower()
            event_city = str(booking.event_city).lower()
            if vendor_city and event_city and vendor_city != event_city:
                booking.ai_context_address = booking.ai_context_address or {}
                booking.ai_context_address["city_mismatch"] = True

        resolved_category_id = normalize_category_id(booking.category_id or (vendor_doc or {}).get("category_id"))
        flow_template = get_booking_flow_template(resolved_category_id)
        booking.category_id = resolved_category_id
        booking.category_flow_version = flow_template.get("flow_version") if flow_template else "generic"

        self._validate_service_address(booking, event_doc)
        if booking.event_address:
            address_payload = (
                booking.event_address.model_dump()
                if hasattr(booking.event_address, "model_dump")
                else booking.event_address
            )
            booking.ai_context_address = address_payload
        elif booking.location or booking.event_city:
            booking.ai_context_address = {
                "address_type": "event",
                "location": booking.location,
                "city": booking.event_city,
            }

        booking.category_booking_details = booking.category_booking_details or {}
        booking.category_booking_details.setdefault("event_date", booking.event_date)
        booking.category_booking_details.setdefault("start_time", booking.start_time)
        booking.category_booking_details.setdefault("event_city", booking.event_city)
        booking.category_booking_details.setdefault("event_location", booking.location)

        if flow_template:
            try:
                booking.category_booking_details = validate_and_normalize_booking_details(
                    resolved_category_id, booking.category_booking_details
                )
            except CategoryBookingValidationError as exc:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid category booking details: {', '.join(exc.errors)}",
                ) from exc

        booking.user_id = current_user.get("sub")
        booking.created_at = datetime.now(timezone.utc)
        booking.updated_at = None

        if booking.vendor_id and booking.items:
            definition = await self.repo.get_service_definition(booking.vendor_id)
            items_map = {i.get("id"): i for i in (definition.get("service_items", []) if definition else [])}
            normalized_items = []
            computed_total = 0.0
            for item in booking.items:
                item_id = item.id
                if item_id not in items_map:
                    raise HTTPException(status_code=400, detail="Invalid item selection")
                db_item = items_map[item_id]
                qty = max(int(item.qty or 1), 1)
                unit_price = float(db_item.get("unit_price", 0))
                total_price = unit_price * qty
                computed_total += total_price
                normalized_items.append(
                    BookingItem(
                        id=item_id,
                        name=db_item.get("name"),
                        qty=qty,
                        unit_price=unit_price,
                        total_price=total_price,
                        notes=item.notes,
                    )
                )
            booking.items = normalized_items
            booking.total_amount = computed_total

        booking.payment_plan = build_payment_plan(booking.total_amount, resolved_category_id)
        booking.pricing_snapshot = {
            "pricing_model": (flow_template or {}).get("pricing_model", "custom"),
            "quoted_total_amount": booking.total_amount,
        }

        booking_doc = booking.model_dump()
        booking_doc["created_at"] = booking_doc["created_at"].isoformat()
        if booking_doc.get("updated_at"):
            booking_doc["updated_at"] = booking_doc["updated_at"].isoformat()

        await self.repo.insert_booking(booking_doc)
        await self.repo.insert_booking_audit_log(
            booking_id=booking_doc["id"],
            actor_id=booking_doc["user_id"],
            actor_role=current_user.get("role"),
            action="created",
            details={"total_amount": booking_doc.get("total_amount")},
        )

        try:
            if booking_doc.get("vendor_id"):
                from email_service import send_vendor_new_quote_request

                vendor = await self.repo.get_vendor(booking_doc.get("vendor_id"))
                if vendor:
                    user = await self.repo.get_user(vendor.get("user_id"))
                    if user:
                        await send_vendor_new_quote_request(
                            user.get("email"),
                            vendor.get("business_name"),
                            "Customer",
                            [i.get("name") for i in booking_doc.get("items", [])],
                        )
        except Exception as exc:
            logger.error(f"Failed to notify vendor for booking: {str(exc)}")

        return booking_doc

    async def vendor_action(
        self,
        booking_id: str,
        action: str,
        reason: Optional[str],
        current_user: Dict[str, Any],
    ) -> Dict[str, Any]:
        user_id = current_user.get("sub")
        vendor_doc = await self.repo.get_vendor_by_user(user_id)
        if not vendor_doc:
            raise HTTPException(status_code=403, detail="Vendor profile not found")

        booking = await self.repo.get_booking(booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.get("vendor_id") != vendor_doc.get("id"):
            raise HTTPException(status_code=403, detail="Not allowed")

        now_iso = datetime.now(timezone.utc).isoformat()
        if action == "accept":
            await self.repo.update_booking(
                booking_id, {"status": BookingStatus.VENDOR_ACCEPTED, "updated_at": now_iso}
            )
            await self.repo.insert_booking_audit_log(booking_id, user_id, "vendor", "accepted")
            try:
                await self.repo.increment_vendor_metrics(vendor_doc.get("id"), delta_accepted=1)
            except Exception as exc:
                logger.error(f"Failed to update vendor metrics on accept: {str(exc)}")
            try:
                user = await self.repo.get_user(booking.get("user_id"))
                if user:
                    from email_service import send_booking_confirmation_email

                    await send_booking_confirmation_email(
                        user.get("email"),
                        user.get("name"),
                        vendor_doc.get("business_name"),
                        booking_id,
                        booking.get("total_amount", 0),
                    )
            except Exception as exc:
                logger.error(f"Failed to notify user on accept: {str(exc)}")
            return {"message": "Booking accepted"}

        if action == "reject":
            await self.repo.update_booking(
                booking_id,
                {
                    "status": BookingStatus.CANCELLED_BY_VENDOR,
                    "updated_at": now_iso,
                    "emergency_reason": reason,
                },
            )
            await self.repo.insert_booking_audit_log(
                booking_id, user_id, "vendor", "rejected", reason=reason
            )
            try:
                await self.repo.increment_vendor_metrics(vendor_doc.get("id"), delta_rejected=1)
            except Exception as exc:
                logger.error(f"Failed to update vendor metrics on reject: {str(exc)}")
            try:
                user = await self.repo.get_user(booking.get("user_id"))
                if user:
                    from email_service import send_booking_cancelled_email

                    await send_booking_cancelled_email(
                        user.get("email"),
                        user.get("name"),
                        vendor_doc.get("business_name"),
                        booking_id,
                        booking.get("total_amount", 0),
                        reason or "Vendor could not fulfill the booking.",
                    )
            except Exception:
                pass
            return {"message": "Booking rejected"}

        raise HTTPException(status_code=400, detail="Invalid action")

    async def vendor_emergency_cancel(
        self,
        booking_id: str,
        payload: Dict[str, Any],
        current_user: Dict[str, Any],
    ) -> Dict[str, Any]:
        user_id = current_user.get("sub")
        vendor_doc = await self.repo.get_vendor_by_user(user_id)
        if not vendor_doc:
            raise HTTPException(status_code=403, detail="Vendor profile not found")

        booking = await self.repo.get_booking(booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.get("vendor_id") != vendor_doc.get("id"):
            raise HTTPException(status_code=403, detail="Not allowed")

        reason = (payload or {}).get("reason")
        notes = (payload or {}).get("notes")
        impact_score = (payload or {}).get("impact_score")
        if not reason or not str(reason).strip():
            raise HTTPException(status_code=400, detail="Reason is required")

        suggestions: List[str] = []
        try:
            from services.replacement_matcher import find_replacement_vendors

            vendor_category = vendor_doc.get("category_id")
            city = booking.get("event_city") or booking.get("location") or vendor_doc.get("city")
            target_price = booking.get("total_amount")
            candidates = await find_replacement_vendors(
                self.repo.db,
                vendor_category,
                city,
                target_price,
                exclude_ids=[vendor_doc.get("id")],
                limit=6,
            )
            suggestions = [c.get("id") for c in candidates]
        except Exception as exc:
            logger.error(f"Replacement suggestions failed: {str(exc)}")

        now_iso = datetime.now(timezone.utc).isoformat()

        async def txn(session):
            await self.repo.update_booking(
                booking_id,
                {
                    "status": BookingStatus.CANCELLED_BY_VENDOR_EMERGENCY,
                    "updated_at": now_iso,
                    "emergency_reason": reason,
                    "emergency_notes": notes,
                    "emergency_notified_admin": True,
                    "impact_score": impact_score,
                    "replacement_suggestions": suggestions,
                },
                session=session,
            )
            await self.repo.insert_booking_audit_log(
                booking_id, user_id, "vendor", "emergency_cancel", reason=reason, session=session
            )
            await self.repo.increment_vendor_metrics(
                vendor_doc.get("id"),
                delta_emergency=1,
                delta_rejected=1,
                reliability_penalty=10,
                visibility_penalty=0.1,
                session=session,
            )

        await self.repo.with_transaction(txn)

        try:
            from email_service import send_emergency_admin_alert

            admin_email = os.environ.get("ADMIN_EMAIL") or os.environ.get("FROM_EMAIL")
            if admin_email:
                await send_emergency_admin_alert(
                    admin_email, vendor_doc.get("business_name"), booking_id, reason
                )
        except Exception as exc:
            logger.error(f"Failed to notify admin of emergency: {str(exc)}")

        try:
            user = await self.repo.get_user(booking.get("user_id"))
            if user:
                from email_service import send_vendor_emergency_cancelled_email

                await send_vendor_emergency_cancelled_email(
                    user.get("email"),
                    user.get("name"),
                    vendor_doc.get("business_name"),
                    booking_id,
                    booking.get("total_amount", 0),
                    reason,
                )
        except Exception as exc:
            logger.error(f"Failed to notify user of emergency: {str(exc)}")

        return {"message": "Emergency cancellation recorded", "suggestions": suggestions}

    async def get_emergency_bookings(self, skip: int, limit: int) -> List[Dict[str, Any]]:
        emergency_bookings = await self.repo.list_emergency_bookings(skip, limit)
        enriched = []
        for booking in emergency_bookings:
            vendor = await self.repo.get_vendor(booking.get("vendor_id"))
            user = await self.repo.get_user(booking.get("user_id"))
            replacement_ids = booking.get("replacement_suggestions", [])
            replacement_vendors = await self.repo.list_vendors_by_ids_minimal(replacement_ids)
            enriched.append(
                {
                    **booking,
                    "booking_id": booking.get("id"),
                    "status": "pending",
                    "vendor_name": vendor.get("business_name") if vendor else "Unknown",
                    "vendor_category": vendor.get("category_id") if vendor else "Unknown",
                    "customer_name": user.get("name") if user else "Unknown",
                    "customer_phone": user.get("phone") if user else None,
                    "customer_email": user.get("email") if user else None,
                    "booking_amount": booking.get("total_amount"),
                    "event_location": booking.get("location") or booking.get("event_city"),
                    "reason": booking.get("emergency_reason"),
                    "replacement_vendors": replacement_vendors,
                    "impact_score": booking.get("impact_score"),
                }
            )
        return enriched

    async def approve_emergency_replacement(
        self, booking_id: str, current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        booking = await self.repo.get_booking(booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.get("status") != BookingStatus.CANCELLED_BY_VENDOR_EMERGENCY:
            raise HTTPException(status_code=400, detail="Not an emergency cancellation")

        suggestions = booking.get("replacement_suggestions", [])
        if not suggestions:
            raise HTTPException(status_code=400, detail="No replacement vendors available")
        replacement_vendor_id = suggestions[0]
        vendor = await self.repo.get_vendor(replacement_vendor_id)
        if not vendor:
            raise HTTPException(status_code=404, detail="Replacement vendor not found")

        new_booking_id = str(uuid.uuid4())
        new_booking = {
            "id": new_booking_id,
            "user_id": booking.get("user_id"),
            "vendor_id": replacement_vendor_id,
            "status": BookingStatus.PENDING,
            "items": booking.get("items", []),
            "total_amount": booking.get("total_amount", 0),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_replacement_for": booking_id,
        }
        now_iso = datetime.now(timezone.utc).isoformat()

        async def txn(session):
            await self.repo.create_replacement_booking_and_resolve_original(
                booking_id,
                new_booking,
                {
                    "status": BookingStatus.RESOLVED,
                    "updated_at": now_iso,
                    "resolution_type": "replacement_approved",
                    "replacement_booking_id": new_booking_id,
                },
                session=session,
            )
            await self.repo.insert_booking_audit_log(
                booking_id,
                current_user.get("sub"),
                "admin",
                "approved_replacement",
                details={"replacement_vendor_id": replacement_vendor_id},
                session=session,
            )

        await self.repo.with_transaction(txn)
        return {"message": "Replacement approved", "new_booking_id": new_booking_id}

    async def initiate_refund(self, booking_id: str, current_user: Dict[str, Any]) -> Dict[str, Any]:
        booking = await self.repo.get_booking(booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.get("status") != BookingStatus.CANCELLED_BY_VENDOR_EMERGENCY:
            raise HTTPException(status_code=400, detail="Not an emergency cancellation")

        now_iso = datetime.now(timezone.utc).isoformat()

        async def txn(session):
            await self.repo.update_booking(
                booking_id,
                {
                    "status": BookingStatus.REFUNDED,
                    "updated_at": now_iso,
                    "resolution_type": "refund_initiated",
                    "refund_initiated_at": now_iso,
                },
                session=session,
            )
            await self.repo.insert_booking_audit_log(
                booking_id,
                current_user.get("sub"),
                "admin",
                "initiated_refund",
                details={"refund_amount": booking.get("total_amount")},
                session=session,
            )

        await self.repo.with_transaction(txn)

        try:
            user = await self.repo.get_user(booking.get("user_id"))
            if user:
                from email_service import send_refund_initiated_email

                await send_refund_initiated_email(
                    user.get("email"), user.get("name"), booking.get("total_amount")
                )
        except Exception as exc:
            logger.error(f"Failed to notify user of refund: {str(exc)}")

        return {"message": "Refund initiated", "refund_amount": booking.get("total_amount")}

    async def escalate_emergency(
        self, booking_id: str, reason: str, current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        booking = await self.repo.get_booking(booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.get("status") != BookingStatus.CANCELLED_BY_VENDOR_EMERGENCY:
            raise HTTPException(status_code=400, detail="Not an emergency cancellation")

        now_iso = datetime.now(timezone.utc).isoformat()
        async def txn(session):
            await self.repo.update_booking(
                booking_id,
                {
                    "status": BookingStatus.ESCALATED,
                    "updated_at": now_iso,
                    "escalation_reason": reason,
                    "escalated_at": now_iso,
                    "escalated_by": current_user.get("sub"),
                },
                session=session,
            )
            await self.repo.insert_booking_audit_log(
                booking_id,
                current_user.get("sub"),
                "admin",
                "escalated",
                reason=reason,
                session=session,
            )
        await self.repo.with_transaction(txn)

        try:
            admin_email = os.environ.get("ADMIN_EMAIL") or os.environ.get("FROM_EMAIL")
            if admin_email:
                from email_service import send_emergency_escalation_email

                vendor = await self.repo.get_vendor(booking.get("vendor_id"))
                user = await self.repo.get_user(booking.get("user_id"))
                await send_emergency_escalation_email(
                    admin_email,
                    booking_id,
                    vendor.get("business_name") if vendor else "Unknown",
                    user.get("name") if user else "Unknown",
                    reason,
                )
        except Exception as exc:
            logger.error(f"Failed to notify admin of escalation: {str(exc)}")

        return {"message": "Emergency escalated for manual review"}

    def _validate_status_transition(
        self, role: Optional[str], old_status: str, new_status: BookingStatus
    ) -> None:
        if role == UserRole.ADMIN:
            return
        if role == UserRole.CUSTOMER:
            if new_status != BookingStatus.CANCELLED_BY_USER:
                raise HTTPException(status_code=403, detail="Not allowed")
            if old_status in {
                BookingStatus.CANCELLED_BY_USER,
                BookingStatus.CANCELLED_BY_VENDOR,
                BookingStatus.CANCELLED_BY_VENDOR_EMERGENCY,
                BookingStatus.REFUNDED,
                BookingStatus.RESOLVED,
                BookingStatus.COMPLETED,
            }:
                raise HTTPException(status_code=400, detail="Invalid status transition")
            return
        if role == UserRole.VENDOR:
            allowed = {BookingStatus.IN_PROGRESS, BookingStatus.COMPLETED}
            if new_status not in allowed:
                raise HTTPException(status_code=403, detail="Not allowed")
            if new_status == BookingStatus.IN_PROGRESS and old_status not in {
                BookingStatus.VENDOR_ACCEPTED,
                BookingStatus.CONFIRMED,
            }:
                raise HTTPException(status_code=400, detail="Invalid status transition")
            if new_status == BookingStatus.COMPLETED and old_status not in {
                BookingStatus.IN_PROGRESS,
                BookingStatus.VENDOR_ACCEPTED,
            }:
                raise HTTPException(status_code=400, detail="Invalid status transition")
            return
        raise HTTPException(status_code=403, detail="Not allowed")

    async def update_booking_status(
        self, booking_id: str, new_status: BookingStatus, current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        booking = await self.repo.get_booking(booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        role = current_user.get("role")
        user_id = current_user.get("sub")

        if role == UserRole.CUSTOMER and booking.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Not allowed")
        if role == UserRole.VENDOR:
            vendor_doc = await self.repo.get_vendor_by_user(user_id)
            if not vendor_doc or vendor_doc.get("id") != booking.get("vendor_id"):
                raise HTTPException(status_code=403, detail="Not allowed")

        old_status = booking.get("status")
        self._validate_status_transition(role, old_status, new_status)
        now_iso = datetime.now(timezone.utc).isoformat()

        async def txn(session):
            await self.repo.update_booking(
                booking_id, {"status": new_status, "updated_at": now_iso}, session=session
            )
            await self.repo.insert_booking_audit_log(
                booking_id,
                user_id,
                role if role else "system",
                f"status_update:{old_status}->{new_status}",
                session=session,
            )
            await self.repo.insert_platform_audit_log(
                action_type="order_status_change",
                performed_by=role if role else "system",
                performed_by_id=user_id,
                entity_type="booking",
                entity_id=booking_id,
                old_value={"status": old_status},
                new_value={"status": new_status},
                session=session,
            )
            if new_status == BookingStatus.COMPLETED and booking.get("vendor_id"):
                await self.repo.increment_vendor_metrics(
                    booking.get("vendor_id"), delta_completed=1, session=session
                )

        await self.repo.with_transaction(txn)
        return {"message": "Status updated", "status": new_status}
