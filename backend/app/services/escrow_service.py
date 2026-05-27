from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import NotFoundError, ValidationError
from app.models.schemas import EscrowBookingRequest, ReleaseMilestoneRequest
from app.services.decision_outcome_service import DecisionOutcomeService
from app.services.vendor_analytics_service import VendorAnalyticsService
from app.utils.ids import oid

logger = logging.getLogger(__name__)


class EscrowService:
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        decision_outcome_service: DecisionOutcomeService,
        vendor_analytics_service: VendorAnalyticsService,
    ) -> None:
        self.db = db
        self.decision_outcome_service = decision_outcome_service
        self.vendor_analytics_service = vendor_analytics_service

    async def create_booking_with_escrow(self, payload: EscrowBookingRequest) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        event_id = oid(payload.event_id)
        user_id = oid(payload.user_id)
        vendor_id = oid(payload.vendor_id)

        amount_sum = round(sum(m.amount for m in payload.milestones), 2)
        if round(payload.total_amount, 2) != amount_sum:
            raise ValidationError("Milestone sum must equal total_amount")

        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                existing = await self.db.bookings.find_one(
                    {"event_id": event_id, "status": {"$in": ["pending", "confirmed", "in_progress"]}},
                    session=session,
                )
                if existing:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Active booking already exists for event")

                decision_snapshot = await self.db.decision_scores.find_one(
                    {"event_id": event_id, "vendor_id": vendor_id},
                    projection={
                        "_id": 1,
                        "score": 1,
                        "components": 1,
                        "recommendation": 1,
                        "model_version": 1,
                        "quoted_price": 1,
                        "created_at": 1,
                    },
                    sort=[("created_at", -1)],
                    session=session,
                )
                booking_id = ObjectId()
                booking_doc = {
                    "_id": booking_id,
                    "event_id": event_id,
                    "user_id": user_id,
                    "vendor_id": vendor_id,
                    "status": "confirmed",
                    "total_amount": payload.total_amount,
                    "currency": payload.currency,
                    "booked_at": now,
                    "created_at": now,
                    "updated_at": now,
                    "metadata": payload.metadata,
                    "decision_snapshot": decision_snapshot,
                }
                await self.db.bookings.insert_one(booking_doc, session=session)

                milestone_docs: List[Dict[str, Any]] = []
                tx_docs: List[Dict[str, Any]] = []
                for m in sorted(payload.milestones, key=lambda x: x.sequence):
                    milestone_id = ObjectId()
                    milestone_doc = {
                        "_id": milestone_id,
                        "booking_id": booking_id,
                        "sequence": m.sequence,
                        "title": m.title,
                        "amount": m.amount,
                        "status": "locked",
                        "due_at": m.due_at,
                        "released_at": None,
                        "created_at": now,
                        "updated_at": now,
                    }
                    milestone_docs.append(milestone_doc)

                    tx_docs.append(
                        {
                            "_id": ObjectId(),
                            "booking_id": booking_id,
                            "vendor_id": vendor_id,
                            "milestone_id": milestone_id,
                            "tx_type": "lock",
                            "amount": m.amount,
                            "currency": payload.currency,
                            "status": "succeeded",
                            "provider_ref": None,
                            "created_at": now,
                            "updated_at": now,
                            "expires_at": now + timedelta(days=180),
                        }
                    )

                await self.db.milestones.insert_many(milestone_docs, session=session, ordered=True)
                await self.db.escrow_transactions.insert_many(tx_docs, session=session, ordered=True)

                await self.db.events.update_one(
                    {"_id": event_id},
                    {"$set": {"status": "booked", "updated_at": now}},
                    session=session,
                )

        logger.info("escrow_booking_created event_id=%s booking_id=%s", payload.event_id, str(booking_id))
        return {
            "booking_id": str(booking_id),
            "status": "confirmed",
            "milestone_count": len(payload.milestones),
            "locked_amount": payload.total_amount,
        }

    async def release_milestone(self, payload: ReleaseMilestoneRequest) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        booking_id = oid(payload.booking_id)
        milestone_id = oid(payload.milestone_id)
        booking_status = "in_progress"
        category = "unknown"
        vendor_id = None
        delayed = False

        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                milestone = await self.db.milestones.find_one(
                    {"_id": milestone_id, "booking_id": booking_id},
                    session=session,
                )
                if not milestone:
                    raise NotFoundError("Milestone not found")
                if milestone["status"] != "locked":
                    raise ValidationError("Milestone is not releasable")

                await self.db.milestones.update_one(
                    {"_id": milestone_id, "status": "locked"},
                    {"$set": {"status": "released", "released_at": now, "updated_at": now}},
                    session=session,
                )

                booking = await self.db.bookings.find_one({"_id": booking_id}, session=session)
                if not booking:
                    raise NotFoundError("Booking not found")
                vendor_id = booking["vendor_id"]
                event = await self.db.events.find_one({"_id": booking["event_id"]}, projection={"categories": 1}, session=session)
                category = (event.get("categories", ["unknown"])[0] if event else "unknown")

                await self.db.escrow_transactions.insert_one(
                    {
                        "_id": ObjectId(),
                        "booking_id": booking_id,
                        "vendor_id": booking["vendor_id"],
                        "milestone_id": milestone_id,
                        "tx_type": "release",
                        "amount": float(milestone["amount"]),
                        "currency": booking["currency"],
                        "status": "succeeded",
                        "provider_ref": None,
                        "created_at": now,
                        "updated_at": now,
                    },
                    session=session,
                )

                pending_count = await self.db.milestones.count_documents(
                    {"booking_id": booking_id, "status": {"$in": ["locked", "pending"]}},
                    session=session,
                )
                booking_status = "completed" if pending_count == 0 else "in_progress"
                await self.db.bookings.update_one(
                    {"_id": booking_id},
                    {"$set": {"status": booking_status, "updated_at": now}},
                    session=session,
                )
                delayed = bool(milestone.get("due_at") and now > milestone["due_at"])

        logger.info("escrow_milestone_released booking_id=%s milestone_id=%s", payload.booking_id, payload.milestone_id)
        if vendor_id is not None:
            await self.vendor_analytics_service.record_milestone_status(
                vendor_id=vendor_id,
                category=category,
                delayed=delayed,
                disputed=False,
            )
        if booking_status == "completed":
            await self.decision_outcome_service.record_booking_outcome(booking_id=booking_id, category=category)
        return {"booking_id": payload.booking_id, "milestone_id": payload.milestone_id, "status": "released"}

    async def trigger_auto_disputes(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        overdue = await self.db.milestones.find(
            {"status": "locked", "due_at": {"$lt": now}},
            projection={"_id": 1, "booking_id": 1, "amount": 1},
        ).to_list(length=5000)

        disputes_created = 0
        for milestone in overdue:
            booking = await self.db.bookings.find_one({"_id": milestone["booking_id"]}, projection={"vendor_id": 1, "currency": 1})
            if not booking:
                continue
            existing_dispute = await self.db.escrow_transactions.find_one(
                {"milestone_id": milestone["_id"], "tx_type": "dispute", "status": "open"}
            )
            if existing_dispute:
                continue
            await self.db.escrow_transactions.insert_one(
                {
                    "_id": ObjectId(),
                    "booking_id": milestone["booking_id"],
                    "vendor_id": booking["vendor_id"],
                    "milestone_id": milestone["_id"],
                    "tx_type": "dispute",
                    "amount": float(milestone["amount"]),
                    "currency": booking.get("currency", "USD"),
                    "status": "open",
                    "provider_ref": None,
                    "created_at": now,
                    "updated_at": now,
                }
            )
            await self.db.milestones.update_one(
                {"_id": milestone["_id"]},
                {"$set": {"status": "disputed", "updated_at": now}},
            )
            await self.vendor_analytics_service.record_milestone_status(
                vendor_id=booking["vendor_id"],
                category="unknown",
                delayed=True,
                disputed=True,
            )
            disputes_created += 1

        logger.info("auto_dispute_scan checked=%s created=%s", len(overdue), disputes_created)
        return {"checked": len(overdue), "created": disputes_created}
