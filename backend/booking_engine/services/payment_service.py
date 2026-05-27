from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from booking_engine.core.booking_orchestrator import BookingOrchestrator
from core.config import get_settings


class PaymentService:
    def __init__(self, db: AsyncIOMotorDatabase, razorpay_client: Any):
        self.db = db
        self.razorpay_client = razorpay_client
        self.settings = get_settings()
        self.orchestrator = BookingOrchestrator(db)

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
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )

    async def create_order(self, *, intent_id: str, idempotency_key: str, current_user: Dict[str, Any]) -> Dict[str, Any]:
        user_id = current_user["sub"]
        scope = "payment_create_order"

        cached = await self._get_idempotent(user_id=user_id, scope=scope, key=idempotency_key)
        if cached:
            return cached

        intent = await self.db.be_booking_intents.find_one(
            {"id": intent_id, "user_id": user_id},
            {"_id": 0},
        )
        if not intent:
            raise HTTPException(status_code=404, detail="Booking intent not found")
        if intent["status"] not in {"awaiting_payment", "payment_pending_verification"}:
            raise HTTPException(status_code=409, detail="Intent not payable in current state")

        amount_paise = int(round(float(intent["payment_summary"]["payable_now"]) * 100))
        receipt = intent_id

        existing_payment = await self.db.be_payments.find_one(
            {"intent_id": intent_id, "status": {"$in": ["created", "captured"]}},
            {"_id": 0},
        )
        if existing_payment and existing_payment.get("razorpay_order_id"):
            response = {
                "order_id": existing_payment["razorpay_order_id"],
                "amount": amount_paise,
                "currency": "INR",
                "key_id": self.settings.RAZORPAY_KEY_ID,
                "intent_id": intent_id,
            }
            await self._save_idempotent(user_id=user_id, scope=scope, key=idempotency_key, response=response)
            return response

        order = self.razorpay_client.order.create(
            {
                "amount": amount_paise,
                "currency": "INR",
                "receipt": receipt,
                "notes": {"intent_id": intent_id, "category_type": intent["category_type"]},
            }
        )

        now = datetime.now(timezone.utc)
        await self.db.be_payments.insert_one(
            {
                "id": f"pay_{intent_id}",
                "intent_id": intent_id,
                "booking_id": None,
                "category_type": intent["category_type"],
                "user_id": user_id,
                "vendor_id": intent["vendor_id"],
                "amount": amount_paise / 100,
                "currency": "INR",
                "status": "created",
                "razorpay_order_id": order["id"],
                "razorpay_payment_id": None,
                "created_at": now,
                "updated_at": now,
            }
        )
        await self.db.be_booking_intents.update_one(
            {"id": intent_id},
            {
                "$set": {
                    "status": "payment_pending_verification",
                    "updated_at": now,
                    "razorpay_order_id": order["id"],
                },
                "$inc": {"version": 1},
            },
        )

        response = {
            "order_id": order["id"],
            "amount": amount_paise,
            "currency": "INR",
            "key_id": self.settings.RAZORPAY_KEY_ID,
            "intent_id": intent_id,
        }
        await self._save_idempotent(user_id=user_id, scope=scope, key=idempotency_key, response=response)
        return response

    async def verify_payment(
        self,
        *,
        intent_id: str,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
        idempotency_key: str,
        current_user: Dict[str, Any],
    ) -> Dict[str, Any]:
        user_id = current_user["sub"]
        scope = "payment_verify"

        cached = await self._get_idempotent(user_id=user_id, scope=scope, key=idempotency_key)
        if cached:
            return cached

        try:
            self.razorpay_client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": razorpay_order_id,
                    "razorpay_payment_id": razorpay_payment_id,
                    "razorpay_signature": razorpay_signature,
                }
            )
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid payment signature")

        now = datetime.now(timezone.utc)
        payment = await self.db.be_payments.find_one_and_update(
            {
                "intent_id": intent_id,
                "razorpay_order_id": razorpay_order_id,
                "status": {"$in": ["created", "authorized"]},
            },
            {
                "$set": {
                    "status": "captured",
                    "razorpay_payment_id": razorpay_payment_id,
                    "verified_at": now,
                    "updated_at": now,
                }
            },
            projection={"_id": 0},
        )
        if not payment:
            existing = await self.db.be_bookings.find_one({"intent_id": intent_id}, {"_id": 0, "id": 1, "status": 1})
            if existing:
                return {
                    "verified": True,
                    "booking_id": existing["id"],
                    "booking_status": existing["status"],
                }
            raise HTTPException(status_code=409, detail="Payment state conflict")

        booking = await self.orchestrator.on_payment_verified(
            intent_id=intent_id,
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            source="verify_api",
        )

        await self.db.be_payments.update_one(
            {"intent_id": intent_id},
            {"$set": {"booking_id": booking["id"], "updated_at": datetime.now(timezone.utc)}},
        )

        response = {
            "verified": True,
            "booking_id": booking["id"],
            "booking_status": booking["status"],
        }
        await self._save_idempotent(user_id=user_id, scope=scope, key=idempotency_key, response=response)
        return response

    def verify_webhook_signature(self, raw_body: bytes, signature: str) -> bool:
        webhook_secret = (
            getattr(self.settings, "RAZORPAY_WEBHOOK_SECRET", None)
            or self.settings.RAZORPAY_KEY_SECRET
        )
        digest = hmac.new(webhook_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(digest, signature)

    async def process_webhook(self, *, raw_body: bytes, signature: str) -> Dict[str, Any]:
        if not self.verify_webhook_signature(raw_body, signature):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

        payload = json.loads(raw_body.decode("utf-8"))
        event = payload.get("event")
        if event != "payment.captured":
            return {"received": True, "ignored": True}

        entity = (((payload.get("payload") or {}).get("payment") or {}).get("entity") or {})
        order_id = entity.get("order_id")
        payment_id = entity.get("id")
        notes = entity.get("notes") or {}
        intent_id = notes.get("intent_id")
        if not intent_id:
            payment_doc = await self.db.be_payments.find_one({"razorpay_order_id": order_id}, {"_id": 0, "intent_id": 1})
            intent_id = payment_doc.get("intent_id") if payment_doc else None

        if not intent_id:
            return {"received": True, "ignored": True}

        await self.db.be_payments.update_one(
            {"intent_id": intent_id, "razorpay_order_id": order_id},
            {
                "$set": {
                    "status": "captured",
                    "razorpay_payment_id": payment_id,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )

        booking = await self.orchestrator.on_payment_verified(
            intent_id=intent_id,
            razorpay_order_id=order_id,
            razorpay_payment_id=payment_id,
            source="webhook",
        )

        return {"received": True, "booking_id": booking["id"]}
