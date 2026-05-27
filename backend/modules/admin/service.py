from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool

from email_service import send_vendor_approval_email, send_vendor_rejection_email
from models import (
    AdminActionType,
    AdminAuditLog,
    PaymentStatus,
    PayoutStatus,
    VendorApprovalAction,
    VendorCommissionUpdate,
    VendorLedgerEntry,
    VendorStatus,
)
from services.audit_logger import log_audit_event

from .repository import AdminRepository

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, repo: AdminRepository, razorpay_client: Any = None):
        self.repo = repo
        self.razorpay_client = razorpay_client

    async def _log_admin_action(
        self,
        admin_id: str,
        action_type: AdminActionType,
        target_type: str,
        target_id: str,
        details: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        success: bool = True,
        ip_address: Optional[str] = None,
        session=None,
    ) -> None:
        log = AdminAuditLog(
            admin_id=admin_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            details=details or {},
            reason=reason,
            success=success,
            ip_address=ip_address,
        )
        log_doc = log.model_dump()
        log_doc["created_at"] = log_doc["created_at"].isoformat()
        await self.repo.insert_admin_audit_log(log_doc, session=session)

    async def get_admin_analytics(self) -> Dict[str, Any]:
        total_users = await self.repo.count_users()
        total_vendors = await self.repo.count_vendors()
        pending_approvals = await self.repo.count_pending_vendors()

        paid_orders = await self.repo.list_confirmed_paid_orders(limit=10000)
        total_revenue = sum(o.get("total_amount", 0) for o in paid_orders)

        six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
        orders = await self.repo.list_confirmed_orders_since(six_months_ago.isoformat(), limit=5000)

        monthly = defaultdict(int)
        for order in orders:
            created = order.get("created_at", "")
            if isinstance(created, str):
                try:
                    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    monthly[dt.strftime("%Y-%m")] += 1
                except (TypeError, ValueError):
                    pass

        category_counts = defaultdict(int)
        vendors = await self.repo.list_approved_vendor_categories(limit=5000)
        for vendor in vendors:
            category_counts[vendor.get("category_id", "unknown")] += 1

        categories = await self.repo.list_vendor_categories(limit=100)
        cat_map = {c["id"]: c["name"] for c in categories}
        category_demand = [{"category": cat_map.get(k, k), "count": v} for k, v in category_counts.items()]

        return {
            "total_users": total_users,
            "total_vendors": total_vendors,
            "pending_vendor_approvals": pending_approvals,
            "total_revenue": total_revenue,
            "monthly_bookings": [{"month": k, "count": v} for k, v in sorted(monthly.items())],
            "category_demand": category_demand,
        }

    async def get_pricing_insights(self) -> Dict[str, Any]:
        vendors = await self.repo.list_vendors_for_pricing(limit=5000)
        base_prices = [v.get("base_price") for v in vendors if v.get("base_price") is not None]
        avg_base_price = round(sum(base_prices) / len(base_prices), 2) if base_prices else 0

        vendors_with_rules = sum(1 for v in vendors if v.get("pricing_rules"))
        category_rule_coverage = defaultdict(int)
        for vendor in vendors:
            if vendor.get("pricing_rules"):
                category_rule_coverage[vendor.get("category_id", "unknown")] += 1

        return {
            "avg_base_price": avg_base_price,
            "vendors_with_pricing_rules": vendors_with_rules,
            "total_vendors": len(vendors),
            "category_rule_coverage": dict(category_rule_coverage),
        }

    async def list_users(self, skip: int, limit: int, search: Optional[str], role: Optional[str]):
        query: Dict[str, Any] = {}
        if search:
            query["$or"] = [
                {"email": {"$regex": search, "$options": "i"}},
                {"name": {"$regex": search, "$options": "i"}},
            ]
        if role:
            query["role"] = role
        return await self.repo.list_users(query, skip, limit)

    async def list_vendors(self, skip: int, limit: int, status: Optional[str], category_id: Optional[str]):
        query: Dict[str, Any] = {}
        if status:
            query["status"] = status
        if category_id:
            query["category_id"] = category_id
        return await self.repo.list_vendors(query, skip, limit)

    async def update_vendor_commission(
        self,
        vendor_id: str,
        payload: VendorCommissionUpdate,
        current_user: Dict[str, Any],
    ) -> Dict[str, Any]:
        vendor_doc = await self.repo.get_vendor(vendor_id)
        if not vendor_doc:
            raise HTTPException(status_code=404, detail="Vendor not found")

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No commission fields provided")

        old_value = {
            "commission_percentage": vendor_doc.get("commission_percentage"),
            "minimum_commission": vendor_doc.get("minimum_commission"),
        }
        await self.repo.update_vendor_fields(vendor_id, update_data)
        updated = await self.repo.get_vendor_commission_fields(vendor_id)

        await log_audit_event(
            self.repo.db,
            action_type="commission_override",
            performed_by="admin",
            performed_by_id=current_user.get("sub"),
            entity_type="vendor",
            entity_id=vendor_id,
            old_value=old_value,
            new_value=update_data,
        )
        return {"status": "success", "vendor_id": vendor_id, **(updated or {})}

    async def platform_earnings_by_category(self) -> Dict[str, Any]:
        ledger_entries = await self.repo.list_vendor_ledger(limit=5000)
        if not ledger_entries:
            return {"categories": [], "total_commission": 0}

        vendor_ids = list({e.get("vendor_id") for e in ledger_entries if e.get("vendor_id")})
        vendors = await self.repo.list_vendors_by_ids(vendor_ids)
        vendor_map = {v["id"]: v.get("category_id") for v in vendors}

        categories = await self.repo.list_vendor_categories(limit=200)
        category_map = {c["id"]: c.get("name") for c in categories}

        totals: Dict[str, Dict[str, Any]] = {}
        total_commission = 0.0
        for entry in ledger_entries:
            cat_id = vendor_map.get(entry.get("vendor_id"), "unknown")
            totals.setdefault(
                cat_id,
                {
                    "category_id": cat_id,
                    "category_name": category_map.get(cat_id, cat_id),
                    "commission_total": 0.0,
                    "order_count": 0,
                },
            )
            totals[cat_id]["commission_total"] += float(entry.get("commission_amount") or 0)
            totals[cat_id]["order_count"] += 1
            total_commission += float(entry.get("commission_amount") or 0)

        categories_payload = [{**v, "commission_total": round(v["commission_total"], 2)} for v in totals.values()]
        return {"categories": categories_payload, "total_commission": round(total_commission, 2)}

    async def pending_payouts(self) -> Dict[str, Any]:
        vendors = await self.repo.list_pending_payout_vendors(limit=200)
        return {"vendors": vendors, "count": len(vendors)}

    async def list_payout_requests(self, skip: int, limit: int):
        return await self.repo.list_payout_requests(skip, limit)

    async def approve_payout(self, payout_id: str, current_user: Dict[str, Any]) -> Dict[str, Any]:
        payout = await self.repo.get_payout(payout_id)
        if not payout:
            raise HTTPException(status_code=404, detail="Payout request not found")
        if payout.get("status") == PayoutStatus.COMPLETED:
            return {"status": "already_completed", "payout": payout}
        if payout.get("status") == PayoutStatus.REJECTED:
            return {"status": "already_rejected", "payout": payout}

        amount = float(payout.get("amount") or 0)
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid payout amount")

        now = datetime.now(timezone.utc).isoformat()
        payout_update = await self.repo.complete_payout_if_pending(payout_id, current_user["sub"], now)
        if payout_update.modified_count == 0:
            updated = await self.repo.get_payout(payout_id)
            return {"status": "already_processed", "payout": updated}

        vendor_update = await self.repo.decrement_vendor_payout_balance(payout["vendor_id"], amount)
        if vendor_update.modified_count == 0:
            await self.repo.reset_payout_to_pending(payout_id)
            raise HTTPException(status_code=400, detail="Insufficient payout balance")

        existing_ledger = await self.repo.get_vendor_ledger_by_payout(payout_id)
        if not existing_ledger:
            ledger_entry = VendorLedgerEntry(
                vendor_id=payout["vendor_id"],
                order_id=None,
                payout_id=payout_id,
                source_type="payout",
                gross_amount=0.0,
                commission_percentage=0.0,
                minimum_commission=0.0,
                commission_amount=0.0,
                net_amount=-amount,
                gateway_fee=0.0,
            ).model_dump()
            ledger_entry["created_at"] = ledger_entry["created_at"].isoformat()
            await self.repo.insert_vendor_ledger(ledger_entry)

        updated = await self.repo.get_payout(payout_id)
        await log_audit_event(
            self.repo.db,
            action_type="payout_approval",
            performed_by="admin",
            performed_by_id=current_user.get("sub"),
            entity_type="payout",
            entity_id=payout_id,
            old_value={"status": payout.get("status"), "amount": payout.get("amount")},
            new_value={"status": PayoutStatus.COMPLETED, "amount": amount},
        )
        return {"status": "success", "payout": updated}

    async def reject_payout(self, payout_id: str, payload: Optional[Dict[str, Any]], current_user: Dict[str, Any]) -> Dict[str, Any]:
        payout = await self.repo.get_payout(payout_id)
        if not payout:
            raise HTTPException(status_code=404, detail="Payout request not found")
        if payout.get("status") == PayoutStatus.COMPLETED:
            return {"status": "already_completed", "payout": payout}
        if payout.get("status") == PayoutStatus.REJECTED:
            return {"status": "already_rejected", "payout": payout}

        admin_note = payload.get("admin_note") if payload and isinstance(payload, dict) else None
        await self.repo.reject_payout_if_pending(payout_id, current_user["sub"], admin_note)

        updated = await self.repo.get_payout(payout_id)
        await log_audit_event(
            self.repo.db,
            action_type="payout_rejection",
            performed_by="admin",
            performed_by_id=current_user.get("sub"),
            entity_type="payout",
            entity_id=payout_id,
            old_value={"status": payout.get("status"), "amount": payout.get("amount")},
            new_value={"status": PayoutStatus.REJECTED, "amount": payout.get("amount"), "admin_note": admin_note},
        )
        return {"status": "success", "payout": updated}

    async def generate_settlement(self, payload: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        vendor_id = payload.get("vendor_id")
        amount = float(payload.get("amount") or 0)
        if not vendor_id or amount <= 0:
            raise HTTPException(status_code=400, detail="vendor_id and amount are required")

        settlement = {
            "id": f"stl_{uuid.uuid4().hex}",
            "vendor_id": vendor_id,
            "amount": amount,
            "status": "generated",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "paid_at": None,
            "admin_id": current_user.get("sub"),
        }
        await self.repo.insert_settlement(settlement)
        await log_audit_event(
            self.repo.db,
            action_type="settlement_generation",
            performed_by="admin",
            performed_by_id=current_user.get("sub"),
            entity_type="settlement",
            entity_id=settlement["id"],
            old_value={},
            new_value=settlement,
        )
        return {"status": "success", "settlement": settlement}

    async def pay_settlement(self, settlement_id: str, current_user: Dict[str, Any]) -> Dict[str, Any]:
        settlement = await self.repo.get_settlement(settlement_id)
        if not settlement:
            raise HTTPException(status_code=404, detail="Settlement not found")
        if settlement.get("status") == "paid":
            return {"status": "already_paid", "settlement": settlement}

        now_iso = datetime.now(timezone.utc).isoformat()
        await self.repo.mark_settlement_paid(settlement_id, now_iso, current_user.get("sub"))
        updated = await self.repo.get_settlement(settlement_id)
        await log_audit_event(
            self.repo.db,
            action_type="settlement_payment",
            performed_by="admin",
            performed_by_id=current_user.get("sub"),
            entity_type="settlement",
            entity_id=settlement_id,
            old_value={"status": settlement.get("status")},
            new_value={"status": "paid"},
        )
        return {"status": "success", "settlement": updated}

    async def approve_vendor(
        self,
        vendor_id: str,
        action: VendorApprovalAction,
        current_user: Dict[str, Any],
        client_ip: Optional[str],
    ) -> Dict[str, Any]:
        vendor_doc = await self.repo.get_vendor(vendor_id)
        if not vendor_doc:
            raise HTTPException(status_code=404, detail="Vendor not found")

        user_doc = await self.repo.get_user(vendor_doc["user_id"])
        if not user_doc:
            raise HTTPException(status_code=404, detail="Vendor user not found")

        now = datetime.now(timezone.utc).isoformat()

        if action.action == "approve":
            async def _txn(session):
                await self.repo.update_vendor_approval_action(
                    vendor_id,
                    {"status": VendorStatus.APPROVED, "approved_at": now, "updated_at": now},
                    session=session,
                )
                await self._log_admin_action(
                    current_user["sub"],
                    AdminActionType.VENDOR_APPROVE,
                    "vendor",
                    vendor_id,
                    details={"vendor_name": vendor_doc.get("business_name")},
                    ip_address=client_ip,
                    session=session,
                )

            await self.repo.with_transaction(_txn)
            try:
                await send_vendor_approval_email(user_doc["email"], vendor_doc["business_name"])
            except Exception as exc:
                logger.error(f"Failed to send approval email: {str(exc)}")
            return {"message": "Vendor approved", "status": VendorStatus.APPROVED}

        if action.action == "reject":
            async def _txn(session):
                await self.repo.update_vendor_approval_action(
                    vendor_id,
                    {"status": VendorStatus.REJECTED, "updated_at": now, "rejection_reason": action.reason},
                    session=session,
                )
                await self._log_admin_action(
                    current_user["sub"],
                    AdminActionType.VENDOR_REJECT,
                    "vendor",
                    vendor_id,
                    details={"vendor_name": vendor_doc.get("business_name")},
                    reason=action.reason,
                    ip_address=client_ip,
                    session=session,
                )

            await self.repo.with_transaction(_txn)
            try:
                await send_vendor_rejection_email(user_doc["email"], vendor_doc["business_name"], action.reason or "")
            except Exception as exc:
                logger.error(f"Failed to send rejection email: {str(exc)}")
            return {"message": "Vendor rejected", "status": VendorStatus.REJECTED}

        if action.action == "suspend":
            async def _txn(session):
                await self.repo.update_vendor_approval_action(
                    vendor_id,
                    {"status": VendorStatus.SUSPENDED, "updated_at": now, "suspension_reason": action.reason},
                    session=session,
                )
                await self._log_admin_action(
                    current_user["sub"],
                    AdminActionType.VENDOR_SUSPEND,
                    "vendor",
                    vendor_id,
                    details={"vendor_name": vendor_doc.get("business_name")},
                    reason=action.reason,
                    ip_address=client_ip,
                    session=session,
                )

            await self.repo.with_transaction(_txn)
            return {"message": "Vendor suspended", "status": VendorStatus.SUSPENDED}

        if action.action == "request_changes":
            async def _txn(session):
                await self.repo.update_vendor_approval_action(
                    vendor_id,
                    {
                        "status": VendorStatus.PENDING,
                        "updated_at": now,
                        "requested_changes_reason": action.reason,
                        "onboarding_status": "needs_changes",
                    },
                    session=session,
                )
                await self._log_admin_action(
                    current_user["sub"],
                    AdminActionType.VENDOR_REQUEST_CHANGES,
                    "vendor",
                    vendor_id,
                    details={"vendor_name": vendor_doc.get("business_name")},
                    reason=action.reason,
                    ip_address=client_ip,
                    session=session,
                )

            await self.repo.with_transaction(_txn)
            return {"message": "Changes requested", "status": VendorStatus.PENDING}

        raise HTTPException(status_code=400, detail="Invalid action. Use approve, reject, suspend, or request_changes")

    async def toggle_featured(
        self,
        vendor_id: str,
        featured: bool,
        current_user: Dict[str, Any],
        client_ip: Optional[str],
    ) -> Dict[str, Any]:
        result = await self.repo.set_vendor_featured(vendor_id, featured, datetime.now(timezone.utc).isoformat())
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Vendor not found")

        await self._log_admin_action(
            current_user["sub"],
            AdminActionType.VENDOR_FEATURED,
            "vendor",
            vendor_id,
            details={"is_featured": featured},
            ip_address=client_ip,
        )
        return {"message": "Featured updated", "is_featured": featured}

    async def verify_vendor(self, vendor_id: str, current_user: Dict[str, Any]) -> Dict[str, Any]:
        vendor_doc = await self.repo.get_vendor(vendor_id)
        if not vendor_doc:
            raise HTTPException(status_code=404, detail="Vendor not found")

        old_value = {
            "verification_status": vendor_doc.get("verification_status"),
            "is_verified": vendor_doc.get("is_verified"),
        }
        result = await self.repo.set_vendor_verified(vendor_id, datetime.now(timezone.utc).isoformat())
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Vendor not found")

        await log_audit_event(
            self.repo.db,
            action_type="vendor_bank_verification_change",
            performed_by="admin",
            performed_by_id=current_user.get("sub"),
            entity_type="vendor",
            entity_id=vendor_id,
            old_value=old_value,
            new_value={"verification_status": "approved", "is_verified": True},
        )
        return {"message": "Vendor verified", "status": "approved"}

    async def list_bookings(self, skip: int, limit: int, status: Optional[str]):
        query: Dict[str, Any] = {}
        if status:
            query["status"] = status
        return await self.repo.list_orders(query, skip, limit)

    async def list_payments(self, skip: int, limit: int):
        return await self.repo.list_payments(skip, limit)

    async def block_user(
        self,
        user_id: str,
        reason: str,
        current_user: Dict[str, Any],
        client_ip: Optional[str],
    ) -> Dict[str, Any]:
        result = await self.repo.block_user(user_id, reason, datetime.now(timezone.utc).isoformat())
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")

        await self._log_admin_action(
            current_user["sub"],
            AdminActionType.USER_BLOCKED,
            "user",
            user_id,
            reason=reason,
            ip_address=client_ip,
        )
        return {"message": "User blocked", "is_active": False}

    async def activate_user(self, user_id: str, current_user: Dict[str, Any], client_ip: Optional[str]) -> Dict[str, Any]:
        result = await self.repo.activate_user(user_id)
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")

        await self._log_admin_action(
            current_user["sub"],
            AdminActionType.USER_ACTIVATED,
            "user",
            user_id,
            ip_address=client_ip,
        )
        return {"message": "User activated", "is_active": True}

    async def get_admin_audit_logs(
        self,
        skip: int,
        limit: int,
        admin_id: Optional[str],
        action_type: Optional[str],
        target_type: Optional[str],
    ):
        query: Dict[str, Any] = {}
        if admin_id:
            query["admin_id"] = admin_id
        if action_type:
            query["action_type"] = action_type
        if target_type:
            query["target_type"] = target_type
        return await self.repo.list_admin_audit_logs(query, skip, limit)

    async def get_platform_audit_logs(
        self,
        skip: int,
        limit: int,
        action_type: Optional[str],
        entity_type: Optional[str],
        performed_by: Optional[str],
        entity_id: Optional[str],
        start_date: Optional[str],
        end_date: Optional[str],
    ):
        query: Dict[str, Any] = {}
        if action_type:
            query["action_type"] = action_type
        if entity_type:
            query["entity_type"] = entity_type
        if performed_by:
            query["performed_by"] = performed_by
        if entity_id:
            query["entity_id"] = entity_id

        if start_date or end_date:
            ts_query: Dict[str, Any] = {}
            if start_date:
                try:
                    dt = datetime.fromisoformat(start_date)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    ts_query["$gte"] = dt.isoformat()
                except Exception:
                    ts_query["$gte"] = start_date
            if end_date:
                try:
                    dt = datetime.fromisoformat(end_date)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    ts_query["$lte"] = dt.isoformat()
                except Exception:
                    ts_query["$lte"] = end_date
            query["timestamp"] = ts_query

        return await self.repo.list_platform_audit_logs(query, skip, limit)

    async def get_vendor_stats(self, vendor_id: str) -> Dict[str, Any]:
        vendor_doc = await self.repo.get_vendor(vendor_id)
        if not vendor_doc:
            raise HTTPException(status_code=404, detail="Vendor not found")

        total_bookings = await self.repo.count_vendor_orders(vendor_id)
        confirmed_bookings = await self.repo.count_vendor_confirmed_orders(vendor_id)

        confirmed_orders = await self.repo.list_vendor_confirmed_order_amounts(vendor_id, limit=10000)
        total_revenue = sum(order.get("total_amount", 0) for order in confirmed_orders)

        reviews = await self.repo.list_vendor_reviews(vendor_id, limit=1000)
        avg_rating = sum(r.get("rating", 0) for r in reviews) / len(reviews) if reviews else 0

        return {
            "vendor_id": vendor_id,
            "business_name": vendor_doc.get("business_name"),
            "total_bookings": total_bookings,
            "confirmed_bookings": confirmed_bookings,
            "total_revenue": total_revenue,
            "average_rating": round(avg_rating, 2),
            "total_reviews": len(reviews),
            "status": vendor_doc.get("status"),
            "is_featured": vendor_doc.get("is_featured", False),
        }

    async def vendors_reliability_report(self, skip: int, limit: int) -> Dict[str, Any]:
        vendors = await self.repo.list_vendor_reliability(skip, limit)
        return {"vendors": vendors, "count": len(vendors)}

    async def refund_payment(
        self,
        payment_id: str,
        reason: str,
        current_user: Dict[str, Any],
        client_ip: Optional[str],
    ) -> Dict[str, Any]:
        if not self.razorpay_client:
            raise HTTPException(status_code=500, detail="Payment client not configured")

        payment_doc = await self.repo.get_payment(payment_id)
        if not payment_doc:
            raise HTTPException(status_code=404, detail="Payment not found")

        if payment_doc.get("status") != PaymentStatus.SUCCESS:
            raise HTTPException(status_code=400, detail="Can only refund successful payments")

        razorpay_payment_id = payment_doc.get("razorpay_payment_id")
        if not razorpay_payment_id:
            raise HTTPException(status_code=400, detail="No Razorpay payment ID found")

        try:
            refund_response = await run_in_threadpool(
                self.razorpay_client.payment.refund,
                razorpay_payment_id,
                {"notes": {"reason": reason}},
            )
            refund_id = refund_response.get("id")
            await self.repo.mark_payment_refunded(
                payment_id,
                refund_id,
                reason,
                datetime.now(timezone.utc).isoformat(),
            )

            await self._log_admin_action(
                current_user["sub"],
                AdminActionType.PAYMENT_REFUND,
                "payment",
                payment_id,
                reason=reason,
                details={"refund_id": refund_id},
                ip_address=client_ip,
            )
            return {"message": "Payment refunded", "refund_id": refund_id}
        except Exception as exc:
            logger.error(f"Refund failed: {str(exc)}")
            raise HTTPException(status_code=400, detail=f"Refund failed: {str(exc)}")
