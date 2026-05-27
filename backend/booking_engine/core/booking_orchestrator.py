from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from booking_engine.handlers.registry import build_handler_registry
from booking_engine.models.booking_models import BookingStatus, CategoryType
from booking_engine.schemas.booking import resolve_create_schema
from booking_engine.services.escrow_service import EscrowService


class BookingOrchestrator:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.registry = build_handler_registry(db)
        self.escrow_service = EscrowService(db)

    async def _get_idempotent(self, *, user_id: str, scope: str, key: str) -> Dict[str, Any] | None:
        doc = await self.db.be_idempotency.find_one(
            {"user_id": user_id, "scope": scope, "key": key},
            {"_id": 0, "response": 1},
        )
        return doc.get("response") if doc else None

    async def _save_idempotent(self, *, user_id: str, scope: str, key: str, response: Dict[str, Any]) -> None:
        now = datetime.now(timezone.utc)
        await self.db.be_idempotency.update_one(
            {"user_id": user_id, "scope": scope, "key": key},
            {
                "$set": {
                    "response": response,
                    "updated_at": now,
                    "expires_at": now + timedelta(days=2),
                },
                "$setOnInsert": {
                    "created_at": now,
                },
            },
            upsert=True,
        )

    async def create_booking_intent(self, payload: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        parsed = resolve_create_schema(payload)
        normalized = parsed.model_dump(mode="json")
        category = CategoryType(normalized["category_type"])
        user_id = current_user["sub"]
        idempotency_key = normalized["idempotency_key"]

        cached = await self._get_idempotent(user_id=user_id, scope="create_booking", key=idempotency_key)
        if cached:
            return cached

        handler = self.registry.get(category)
        if not handler:
            raise HTTPException(status_code=422, detail="Unsupported category")

        await handler.validate_create(normalized, current_user)

        intent_id = f"intent_{uuid.uuid4().hex[:16]}"
        reservation = await handler.reserve_resources(normalized, intent_id, ttl_seconds=15 * 60)
        reservation["intent_id"] = intent_id

        event_id = normalized.get("event_id")
        if category == CategoryType.SERVICE and not event_id:
            event_id = await self._create_draft_event(current_user=current_user, payload=normalized)

        payment_summary = handler.payment_summary(normalized)
        now = datetime.now(timezone.utc)

        intent_doc = {
            "id": intent_id,
            "category_type": category.value,
            "user_id": user_id,
            "vendor_id": normalized["vendor_id"],
            "event_id": event_id,
            "payload": normalized,
            "reservation": reservation,
            "payment_summary": payment_summary,
            "status": BookingStatus.AWAITING_PAYMENT.value,
            "version": 1,
            "requires_vendor_acceptance": handler.requires_vendor_acceptance(),
            "uses_escrow": handler.uses_escrow(),
            "created_at": now,
            "updated_at": now,
            "expires_at": now + timedelta(minutes=15),
        }
        await self.db.be_booking_intents.insert_one(intent_doc)

        response = {
            "intent_id": intent_id,
            "booking_id": None,
            "state": BookingStatus.AWAITING_PAYMENT.value,
            "category_type": category.value,
            "requires_payment": True,
            "payment_payload": {
                "amount": int(round(float(payment_summary["payable_now"]) * 100)),
                "currency": payment_summary["currency"],
                "create_order_endpoint": "/api/booking-engine/payments/create-order",
            },
        }
        await self._save_idempotent(user_id=user_id, scope="create_booking", key=idempotency_key, response=response)
        return response

    async def on_payment_verified(
        self,
        *,
        intent_id: str,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        source: str,
    ) -> Dict[str, Any]:
        intent = await self.db.be_booking_intents.find_one({"id": intent_id}, {"_id": 0})
        if not intent:
            raise HTTPException(status_code=404, detail="Booking intent not found")

        if intent["status"] in {
            BookingStatus.TOKEN_PAID.value,
            BookingStatus.VENDOR_PENDING.value,
            BookingStatus.CONFIRMED.value,
        }:
            existing = await self.db.be_bookings.find_one({"intent_id": intent_id}, {"_id": 0})
            if existing:
                return existing

        if intent["status"] not in {
            BookingStatus.AWAITING_PAYMENT.value,
            BookingStatus.PAYMENT_PENDING_VERIFICATION.value,
        }:
            raise HTTPException(status_code=409, detail="Intent not payable in current state")

        now = datetime.now(timezone.utc)
        transition_status = BookingStatus.TOKEN_PAID.value
        await self.db.be_booking_intents.update_one(
            {"id": intent_id, "version": intent["version"]},
            {
                "$set": {
                    "status": transition_status,
                    "updated_at": now,
                    "payment": {
                        "razorpay_order_id": razorpay_order_id,
                        "razorpay_payment_id": razorpay_payment_id,
                        "verified_by": source,
                        "verified_at": now,
                    },
                },
                "$inc": {"version": 1},
            },
        )

        category = CategoryType(intent["category_type"])
        requires_vendor_acceptance = bool(intent.get("requires_vendor_acceptance", False))
        initial_booking_status = (
            BookingStatus.VENDOR_PENDING.value if requires_vendor_acceptance else BookingStatus.CONFIRMED.value
        )

        booking_doc = {
            "id": f"book_{uuid.uuid4().hex[:16]}",
            "intent_id": intent_id,
            "category_type": category.value,
            "user_id": intent["user_id"],
            "vendor_id": intent["vendor_id"],
            "event_id": intent.get("event_id"),
            "payload": intent["payload"],
            "payment_summary": intent["payment_summary"],
            "status": initial_booking_status,
            "version": 1,
            "reservation": intent.get("reservation"),
            "created_at": now,
            "updated_at": now,
        }

        existing = await self.db.be_bookings.find_one({"intent_id": intent_id}, {"_id": 0})
        if existing:
            return existing

        await self.db.be_bookings.insert_one(booking_doc)

        if category == CategoryType.SERVICE:
            await self.escrow_service.capture_service_token(
                booking_id=booking_doc["id"],
                vendor_id=booking_doc["vendor_id"],
                amount=float(intent["payment_summary"]["payable_now"]),
                payment_id=razorpay_payment_id,
            )

        await self.db.be_state_transitions.insert_one(
            {
                "booking_id": booking_doc["id"],
                "category_type": category.value,
                "from_status": BookingStatus.TOKEN_PAID.value,
                "to_status": booking_doc["status"],
                "actor": "system",
                "actor_id": "payment_engine",
                "reason": "Payment verified",
                "created_at": now,
            }
        )

        return booking_doc

    async def _create_draft_event(self, *, current_user: Dict[str, Any], payload: Dict[str, Any]) -> str:
        event_id = f"evt_{uuid.uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)
        await self.db.events.insert_one(
            {
                "id": event_id,
                "user_id": current_user["sub"],
                "title": "Draft Event",
                "date": payload.get("event_date"),
                "location": payload.get("event_location"),
                "city": payload.get("event_city"),
                "is_draft": True,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }
        )
        return event_id
