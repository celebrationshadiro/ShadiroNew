from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict
import uuid

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool

from email_service import send_booking_confirmation_email
from models import OrderStatus, Payment, PaymentStatus, VendorLedgerEntry
from services.commission_engine import build_commission_breakdown

from .repository import PaymentRepository

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, repo: PaymentRepository, razorpay_client: Any, razorpay_key_id: str):
        self.repo = repo
        self.razorpay_client = razorpay_client
        self.razorpay_key_id = razorpay_key_id

    async def create_order(self, order_id: str, current_user: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(
            "payment_create_order_requested",
            extra={"event": "payment_create_order", "module": "payments"},
        )
        order_doc = await self.repo.get_order(order_id)
        if not order_doc:
            raise HTTPException(status_code=404, detail="Order not found")
        if order_doc.get("user_id") != current_user.get("sub"):
            raise HTTPException(status_code=403, detail="Not authorized")
        if order_doc.get("status") == OrderStatus.CONFIRMED or order_doc.get("payment_id"):
            raise HTTPException(status_code=400, detail="Order already paid")

        existing_razorpay_order_id = order_doc.get("razorpay_order_id")
        if existing_razorpay_order_id:
            return {
                "razorpay_order_id": existing_razorpay_order_id,
                "amount": int(float(order_doc["total_amount"]) * 100),
                "currency": "INR",
                "key_id": self.razorpay_key_id,
            }

        payload = {
            "amount": int(float(order_doc["total_amount"]) * 100),
            "currency": "INR",
            "receipt": order_id,
            "notes": {"order_id": order_id},
        }
        razorpay_order = await run_in_threadpool(self.razorpay_client.order.create, payload)

        await self.repo.set_razorpay_order_id(order_id, razorpay_order["id"])
        logger.info(
            "payment_order_created",
            extra={"event": "payment_order_created", "module": "payments"},
        )
        return {
            "razorpay_order_id": razorpay_order["id"],
            "amount": razorpay_order["amount"],
            "currency": razorpay_order["currency"],
            "key_id": self.razorpay_key_id,
        }

    async def verify_order_payment(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
        order_id: str,
        current_user: Dict[str, Any],
    ) -> Dict[str, Any]:
        logger.info(
            "payment_verify_requested",
            extra={"event": "payment_verify", "module": "payments"},
        )
        order_doc = await self.repo.get_order(order_id)
        if not order_doc:
            raise HTTPException(status_code=404, detail="Order not found")
        if order_doc.get("user_id") != current_user.get("sub"):
            raise HTTPException(status_code=403, detail="Not authorized")
        if order_doc.get("status") == OrderStatus.CONFIRMED or order_doc.get("payment_id"):
            raise HTTPException(status_code=400, detail="Order already confirmed")

        expected_razorpay_order_id = order_doc.get("razorpay_order_id")
        if not expected_razorpay_order_id or expected_razorpay_order_id != razorpay_order_id:
            raise HTTPException(status_code=400, detail="Invalid order mapping")

        existing_payment = await self.repo.find_payment_by_razorpay_payment_id(razorpay_payment_id)
        if existing_payment:
            raise HTTPException(status_code=400, detail="Payment already processed")

        params_dict = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        }
        await run_in_threadpool(self.razorpay_client.utility.verify_payment_signature, params_dict)
        logger.info(
            "payment_signature_verified",
            extra={"event": "payment_signature_verified", "module": "payments"},
        )

        payment = Payment(
            order_id=order_id,
            user_id=current_user["sub"],
            amount=float(order_doc.get("total_amount") or 0),
            status=PaymentStatus.SUCCESS,
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
        )
        payment_doc = payment.model_dump()
        payment_doc["created_at"] = payment_doc["created_at"].isoformat()
        vendor_doc = None
        breakdown = None
        if order_doc.get("vendor_id"):
            vendor_doc = await self.repo.get_vendor(order_doc.get("vendor_id"))
            if vendor_doc:
                breakdown = build_commission_breakdown(vendor_doc, float(order_doc.get("total_amount") or 0))

        async def _txn(session):
            await self.repo.insert_payment(payment_doc, session=session)

            order_update = await self.repo.confirm_order_if_pending(order_id, payment.id, session=session)
            if order_update.modified_count != 1:
                raise HTTPException(status_code=400, detail="Order already confirmed")

            audit_doc = {
                "id": str(uuid.uuid4()),
                "action_type": "order_status_change",
                "performed_by": "system",
                "entity_type": "order",
                "entity_id": order_id,
                "old_value": {"status": order_doc.get("status")},
                "new_value": {"status": OrderStatus.CONFIRMED},
                "performed_by_id": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self.repo.insert_audit_log(audit_doc, session=session)

            if vendor_doc and breakdown:
                commission_amount = breakdown["commission_amount"]
                net_amount = breakdown["net_amount"]
                gateway_fee = breakdown["gateway_fee"]

                await self.repo.increment_vendor_payout_balance(vendor_doc.get("id"), net_amount, session=session)
                await self.repo.update_order_commission_fields(
                    order_id,
                    {
                        "commission_percentage": breakdown["commission_percentage"],
                        "minimum_commission": breakdown["minimum_commission"],
                        "commission_amount": commission_amount,
                        "vendor_payout_amount": net_amount,
                        "gateway_fee": gateway_fee,
                    },
                    session=session,
                )

                ledger_entry = VendorLedgerEntry(
                    vendor_id=vendor_doc.get("id"),
                    order_id=order_id,
                    source_type="service_order",
                    gross_amount=float(order_doc.get("total_amount") or 0),
                    commission_percentage=breakdown["commission_percentage"],
                    minimum_commission=breakdown["minimum_commission"],
                    commission_amount=commission_amount,
                    net_amount=net_amount,
                    gateway_fee=gateway_fee,
                ).model_dump()
                ledger_entry["reference_id"] = f"service_order:{order_id}"
                ledger_entry["created_at"] = ledger_entry["created_at"].isoformat()
                await self.repo.insert_vendor_ledger(ledger_entry, session=session)

        try:
            await self.repo.with_transaction(_txn)
        except DuplicateKeyError:
            logger.error(
                "payment_duplicate_detected",
                extra={"event": "payment_duplicate", "module": "payments"},
            )
            raise HTTPException(status_code=400, detail="Payment already processed")
        except Exception:
            logger.exception(
                "payment_transaction_failed",
                extra={"event": "payment_txn_failed", "module": "payments"},
            )
            raise

        try:
            user_doc = await self.repo.get_user(current_user["sub"])
            vendor_doc = await self.repo.get_vendor(order_doc.get("vendor_id"))
            if user_doc and vendor_doc:
                await send_booking_confirmation_email(
                    user_doc["email"],
                    user_doc["name"],
                    vendor_doc["business_name"],
                    order_id,
                    order_doc["total_amount"],
                )
        except Exception as e:
            logger.error(
                f"Failed to send booking confirmation email: {str(e)}",
                extra={"event": "payment_post_email_failed", "module": "payments"},
            )

        logger.info(
            "payment_verified_success",
            extra={"event": "payment_verified", "module": "payments"},
        )
        return {"status": "success", "message": "Payment verified successfully"}
