from __future__ import annotations

import hashlib
import time
from typing import Any, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from canonical_models.common import BookingIntentStatus, BookingStatus, LedgerEntryType, utcnow
from core.config import get_settings
from core.prometheus import increment_webhook_event, observe_payment_latency
from core.settlement import SettlementService


class PaymentExecutionService:
    def __init__(self, db: AsyncIOMotorDatabase, razorpay_client):
        self.db = db
        self.razorpay_client = razorpay_client
        self.settings = get_settings()

    async def process_payment_captured_webhook(
        self,
        *,
        event_id: str,
        event: str,
        payload: dict[str, Any],
        signature: str,
        request_id: str,
        app_state: Any | None = None,
    ) -> dict[str, Any]:
        started_at = time.perf_counter()
        if event != "payment.captured":
            increment_webhook_event(event, "ignored_event")
            return {"processed": False, "reason": "ignored_event_type", "event": event}

        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        razorpay_order_id = str(payment_entity.get("order_id") or "")
        razorpay_payment_id = str(payment_entity.get("id") or "")
        if not razorpay_order_id:
            increment_webhook_event(event, "ignored_missing_order")
            return {"processed": False, "reason": "missing_order_id", "event": event}

        raw_hash = hashlib.sha256(str(payload).encode("utf-8")).hexdigest()
        signature_hash = hashlib.sha256(signature.encode("utf-8")).hexdigest()

        async with await self.db.client.start_session() as session:
            try:
                async with session.start_transaction():
                    await self.db.webhook_events.insert_one(
                        {
                            "id": f"wbe_{uuid4().hex}",
                            "event_id": event_id,
                            "event": event,
                            "request_id": request_id,
                            "signature_hash": signature_hash,
                            "payload_hash": raw_hash,
                            "received_at": utcnow(),
                            "status": "PROCESSING",
                        },
                        session=session,
                    )
            except DuplicateKeyError:
                increment_webhook_event(event, "replay")
                observe_payment_latency("webhook", time.perf_counter() - started_at)
                return {"processed": True, "idempotent_replay": True, "event_id": event_id}

            async with session.start_transaction():
                payment = await self.db.payments.find_one(
                    {"razorpay_order_id": razorpay_order_id},
                    {"_id": 0},
                    session=session,
                )
                if not payment:
                    await self.db.webhook_events.update_one(
                        {"event_id": event_id},
                        {"$set": {"status": "IGNORED_ORDER_NOT_FOUND", "updated_at": utcnow()}},
                        session=session,
                    )
                    increment_webhook_event(event, "ignored_missing_payment")
                    observe_payment_latency("webhook", time.perf_counter() - started_at)
                    return {"processed": False, "reason": "payment_not_found"}

                payment_update = {
                    "status": "CONFIRMED",
                    "razorpay_payment_id": razorpay_payment_id or payment.get("razorpay_payment_id"),
                    "razorpay_signature": signature,
                    "webhook_received_at": utcnow(),
                    "updated_at": utcnow(),
                }
                payment = await self.db.payments.find_one_and_update(
                    {"id": payment["id"]},
                    {"$set": payment_update},
                    return_document=ReturnDocument.AFTER,
                    projection={"_id": 0},
                    session=session,
                )
                if not payment:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment update conflict")

                intent_id = payment.get("booking_intent_id")
                if not intent_id:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment missing booking intent")
                intent = await self.db.booking_intents.find_one({"id": intent_id}, {"_id": 0}, session=session)
                if not intent:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking intent not found")

                booking = await self._materialize_booking_from_intent(
                    intent=intent,
                    payment=payment,
                    source="webhook",
                    session=session,
                )

                await self.db.webhook_events.update_one(
                    {"event_id": event_id},
                    {
                        "$set": {
                            "status": "PROCESSED",
                            "payment_id": payment["id"],
                            "booking_id": booking["id"],
                            "updated_at": utcnow(),
                        }
                    },
                    session=session,
                )

        if app_state is not None:
            from integrations.grocery_delivery_bridge import try_spawn_grocery_delivery_after_paid_booking

            await try_spawn_grocery_delivery_after_paid_booking(
                db=self.db,
                app_state=app_state,
                booking=booking,
                intent=intent,
                settings=self.settings,
            )

        increment_webhook_event(event, "processed")
        observe_payment_latency("webhook", time.perf_counter() - started_at)
        return {
            "processed": True,
            "event": event,
            "payment_id": payment["id"],
            "booking_id": booking["id"],
            "payment_status": payment["status"],
            "booking_status": booking["status"],
        }

    async def execute_booking_payout(
        self,
        *,
        booking: dict[str, Any],
        actor_id: str,
        idempotency_key: str,
        request_id: str,
    ) -> dict[str, Any]:
        started_at = time.perf_counter()
        booking_id = str(booking.get("id") or "")
        if not booking_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid booking id")

        existing = await self.db.payouts.find_one(
            {"idempotency_key": idempotency_key},
            {"_id": 0},
        )
        if existing and existing.get("status") == "PROCESSED":
            observe_payment_latency("payout", time.perf_counter() - started_at)
            return existing

        payment = await self.db.payments.find_one(
            {"booking_id": booking_id, "status": "CONFIRMED"},
            {"_id": 0},
        )
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Payout requires confirmed Razorpay payment first",
            )

        vendor = await self.db.vendors.find_one(
            {"id": booking.get("vendor_id")},
            {"_id": 0, "razorpay_fund_account_id": 1, "bank_account_last4": 1},
        )
        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
        fund_account_id = str(vendor.get("razorpay_fund_account_id") or "").strip()
        if not fund_account_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vendor payout account is not configured",
            )
        if not self.settings.RAZORPAY_PAYOUT_ACCOUNT_NUMBER:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="RAZORPAY_PAYOUT_ACCOUNT_NUMBER is not configured",
            )

        amount_paise = int(
            booking.get("vendor_net_paise")
            or max(
                int(booking.get("amount_gross_paise", 0) or 0) - int(booking.get("commission_amount_paise", 0) or 0),
                0,
            )
        )
        if amount_paise <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payout amount")

        payout_doc = {
            "id": f"po_{uuid4().hex}",
            "booking_id": booking_id,
            "vendor_id": str(booking.get("vendor_id") or ""),
            "amount_paise": amount_paise,
            "status": "PROCESSING",
            "idempotency_key": idempotency_key,
            "requested_by": actor_id,
            "request_id": request_id,
            "created_at": utcnow(),
            "updated_at": utcnow(),
            "razorpay_payout_id": None,
            "error_message": None,
        }
        if not existing:
            try:
                await self.db.payouts.insert_one(payout_doc)
            except DuplicateKeyError:
                existing = await self.db.payouts.find_one({"idempotency_key": idempotency_key}, {"_id": 0})
                if existing and existing.get("status") == "PROCESSED":
                    observe_payment_latency("payout", time.perf_counter() - started_at)
                    return existing
                if existing:
                    payout_doc = existing
        else:
            payout_doc = existing

        try:
            provider_payload = {
                "account_number": self.settings.RAZORPAY_PAYOUT_ACCOUNT_NUMBER,
                "fund_account_id": fund_account_id,
                "amount": amount_paise,
                "currency": "INR",
                "mode": "IMPS",
                "purpose": "payout",
                "queue_if_low_balance": True,
                "reference_id": booking_id,
                "narration": "Booking settlement payout",
            }
            provider_result = await run_in_threadpool(self.razorpay_client.payout.create, provider_payload)
        except Exception as exc:
            await self.db.payouts.update_one(
                {"id": payout_doc["id"]},
                {
                    "$set": {
                        "status": "FAILED",
                        "error_message": str(exc),
                        "updated_at": utcnow(),
                    }
                },
            )
            observe_payment_latency("payout", time.perf_counter() - started_at)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Razorpay payout request failed") from exc

        provider_status = str(provider_result.get("status") or "").lower()
        provider_payout_id = str(provider_result.get("id") or "")
        if provider_status != "processed":
            await self.db.payouts.update_one(
                {"id": payout_doc["id"]},
                {
                    "$set": {
                        "status": "FAILED",
                        "razorpay_payout_id": provider_payout_id or None,
                        "error_message": f"payout_not_confirmed:{provider_status or 'unknown'}",
                        "updated_at": utcnow(),
                    }
                },
            )
            observe_payment_latency("payout", time.perf_counter() - started_at)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Razorpay payout was not confirmed as processed",
            )

        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                updated = await self.db.payouts.find_one_and_update(
                    {"id": payout_doc["id"]},
                    {
                        "$set": {
                            "status": "PROCESSED",
                            "processed_by": actor_id,
                            "processed_at": utcnow(),
                            "razorpay_payout_id": provider_payout_id,
                            "updated_at": utcnow(),
                        }
                    },
                    return_document=ReturnDocument.AFTER,
                    projection={"_id": 0},
                    session=session,
                )
                if not updated:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payout update conflict")

                await self.db.bookings.update_one(
                    {"id": booking_id},
                    {
                        "$set": {
                            "payout_id": updated["id"],
                            "payout_status": "PROCESSED",
                            "updated_at": utcnow(),
                        }
                    },
                    session=session,
                )

        observe_payment_latency("payout", time.perf_counter() - started_at)
        return updated

    async def execute_vendor_payout(
        self,
        *,
        payout_id: str,
        actor_id: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        started_at = time.perf_counter()
        replay = await self.db.payouts.find_one({"idempotency_key": idempotency_key}, {"_id": 0})
        if replay and replay.get("status") == "PROCESSED":
            observe_payment_latency("vendor_payout", time.perf_counter() - started_at)
            return replay

        payout = await self.db.payouts.find_one({"id": payout_id}, {"_id": 0})
        if not payout:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payout request not found")
        if payout.get("status") == "PROCESSED":
            observe_payment_latency("vendor_payout", time.perf_counter() - started_at)
            return payout
        if payout.get("status") not in {"PENDING", "APPROVED", "PROCESSING"}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payout is not processable")

        vendor_id = str(payout.get("vendor_id") or "")
        amount_paise = int(payout.get("amount_paise", 0) or 0)
        if amount_paise <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payout amount")

        vendor = await self.db.vendors.find_one(
            {"id": vendor_id},
            {"_id": 0, "razorpay_fund_account_id": 1},
        )
        if not vendor or not vendor.get("razorpay_fund_account_id"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vendor payout account missing")
        if not self.settings.RAZORPAY_PAYOUT_ACCOUNT_NUMBER:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="RAZORPAY_PAYOUT_ACCOUNT_NUMBER is not configured",
            )

        await self.db.payouts.update_one(
            {"id": payout_id},
            {
                "$set": {
                    "status": "PROCESSING",
                    "idempotency_key": idempotency_key,
                    "approved_by": actor_id,
                    "approved_at": utcnow(),
                    "updated_at": utcnow(),
                }
            },
        )

        try:
            provider_payload = {
                "account_number": self.settings.RAZORPAY_PAYOUT_ACCOUNT_NUMBER,
                "fund_account_id": vendor["razorpay_fund_account_id"],
                "amount": amount_paise,
                "currency": "INR",
                "mode": "IMPS",
                "purpose": "payout",
                "queue_if_low_balance": True,
                "reference_id": payout_id,
                "narration": "Vendor wallet payout",
            }
            provider_result = await run_in_threadpool(self.razorpay_client.payout.create, provider_payload)
        except Exception as exc:
            await self.db.payouts.update_one(
                {"id": payout_id},
                {"$set": {"status": "FAILED", "error_message": str(exc), "updated_at": utcnow()}},
            )
            observe_payment_latency("vendor_payout", time.perf_counter() - started_at)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Payout request failed") from exc

        provider_status = str(provider_result.get("status") or "").lower()
        if provider_status != "processed":
            await self.db.payouts.update_one(
                {"id": payout_id},
                {
                    "$set": {
                        "status": "FAILED",
                        "razorpay_payout_id": provider_result.get("id"),
                        "error_message": f"payout_not_confirmed:{provider_status or 'unknown'}",
                        "updated_at": utcnow(),
                    }
                },
            )
            observe_payment_latency("vendor_payout", time.perf_counter() - started_at)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Razorpay payout not confirmed")

        settlement = SettlementService(self.db)
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                await settlement.credit_vendor_ledger(
                    vendor_id=vendor_id,
                    amount_paise=amount_paise,
                    booking_id=f"payout:{payout_id}",
                    note="Payout processed; hold released",
                    entry_type=LedgerEntryType.RELEASE,
                    session=session,
                )
                await settlement.credit_vendor_ledger(
                    vendor_id=vendor_id,
                    amount_paise=amount_paise,
                    booking_id=f"payout:{payout_id}",
                    note="Payout transfer processed",
                    entry_type=LedgerEntryType.DEBIT,
                    session=session,
                )
                updated = await self.db.payouts.find_one_and_update(
                    {"id": payout_id},
                    {
                        "$set": {
                            "status": "PROCESSED",
                            "processed_by": actor_id,
                            "processed_at": utcnow(),
                            "razorpay_payout_id": provider_result.get("id"),
                            "updated_at": utcnow(),
                        }
                    },
                    projection={"_id": 0},
                    return_document=ReturnDocument.AFTER,
                    session=session,
                )
                if not updated:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payout update conflict")
        observe_payment_latency("vendor_payout", time.perf_counter() - started_at)
        return updated

    async def _materialize_booking_from_intent(
        self,
        *,
        intent: dict[str, Any],
        payment: dict[str, Any],
        source: str,
        session,
    ) -> dict[str, Any]:
        existing = await self.db.bookings.find_one({"intent_id": intent["id"]}, {"_id": 0}, session=session)
        if existing:
            await self.db.payments.update_one(
                {"id": payment["id"]},
                {"$set": {"booking_id": existing["id"], "updated_at": utcnow()}},
                session=session,
            )
            return existing

        gross = int(intent.get("total_amount_paise", 0) or 0)
        if gross <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid intent amount")
        rate_bps = await self._resolve_commission_bps(intent.get("vendor_id"), session=session)
        commission = (gross * rate_bps) // 10000
        vendor_net = gross - commission
        now = utcnow()

        booking_doc = {
            "id": f"book_{uuid4().hex}",
            "intent_id": intent["id"],
            "user_id": intent.get("user_id"),
            "vendor_id": intent.get("vendor_id"),
            "category_type": intent.get("category_type"),
            "items": intent.get("items", []),
            "status": BookingStatus.PAYMENT_RECEIVED.value,
            "version": 1,
            "scheduled_at": intent.get("scheduled_at"),
            "duration_minutes": intent.get("duration_minutes"),
            "amount_gross_paise": gross,
            "commission_rate_bps": rate_bps,
            "commission_amount_paise": commission,
            "vendor_net_paise": vendor_net,
            "payment_id": payment["id"],
            "resource_lock_ids": [],
            "notes": intent.get("notes"),
            "meta": {**(intent.get("meta") or {}), "payment_source": source},
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
            "cancelled_at": None,
        }
        await self.db.bookings.insert_one(booking_doc, session=session)
        await self.db.booking_intents.update_one(
            {"id": intent["id"], "status": BookingIntentStatus.PENDING.value},
            {"$set": {"status": BookingIntentStatus.CONVERTED.value, "updated_at": now}, "$inc": {"version": 1}},
            session=session,
        )
        await self.db.payments.update_one(
            {"id": payment["id"]},
            {"$set": {"booking_id": booking_doc["id"], "updated_at": now}},
            session=session,
        )
        await self.db.state_transitions.insert_one(
            {
                "id": f"st_{uuid4().hex}",
                "entity_type": "BOOKING",
                "entity_id": booking_doc["id"],
                "from_status": BookingStatus.AWAITING_PAYMENT.value,
                "to_status": BookingStatus.PAYMENT_RECEIVED.value,
                "actor_role": "system",
                "actor_id": "system",
                "reason": f"Payment confirmed via {source}",
                "created_at": now,
            },
            session=session,
        )

        # Invalidate availability cache immediately
        try:
            from core.cache import get_cache_service
            cache = get_cache_service()
            await cache.delete_pattern(f"availability:{intent['vendor_id']}:*")
        except Exception as cache_err:
            logger.error(f"Failed to invalidate availability cache: {cache_err}")

        # Enqueue background jobs for notifications and cache count rebuilds
        try:
            from workers.job_queue import enqueue_job
            await enqueue_job("send_booking_confirmation_email", booking_doc["id"])
            await enqueue_job("send_vendor_new_booking_alert", booking_doc["id"])
            await enqueue_job("update_vendor_booking_count", intent.get("vendor_id"))
        except Exception as queue_err:
            logger.error(f"Failed to enqueue booking confirmed background jobs: {queue_err}")

        return booking_doc

    async def _resolve_commission_bps(self, vendor_id: Optional[str], session) -> int:
        if not vendor_id:
            return 1000
        vendor = await self.db.vendors.find_one(
            {"id": vendor_id},
            {"_id": 0, "commission_override_bps": 1, "category_id": 1},
            session=session,
        )
        if not vendor:
            return 1000
        override = vendor.get("commission_override_bps")
        if isinstance(override, int) and 0 <= override <= 10000:
            return override

        category_id = vendor.get("category_id")
        if category_id:
            category = await self.db.vendor_categories.find_one(
                {"id": category_id},
                {"_id": 0, "default_commission_bps": 1},
                session=session,
            )
            cat_rate = (category or {}).get("default_commission_bps")
            if isinstance(cat_rate, int) and 0 <= cat_rate <= 10000:
                return cat_rate

        config = await self.db.platform_config.find_one(
            {"key": "commission_defaults"},
            {"_id": 0, "default_commission_bps": 1},
            session=session,
        )
        cfg_rate = (config or {}).get("default_commission_bps")
        if isinstance(cfg_rate, int) and 0 <= cfg_rate <= 10000:
            return cfg_rate
        return 1000
