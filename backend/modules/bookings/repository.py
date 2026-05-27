from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase


class BookingRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_booking(self, booking_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.bookings.find_one({"id": booking_id}, {"_id": 0})

    async def get_vendor_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.vendors.find_one({"user_id": user_id}, {"_id": 0})

    async def list_bookings(self, query: Dict[str, Any], skip: int, limit: int) -> List[Dict[str, Any]]:
        cursor = self.db.bookings.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(limit)

    async def get_vendor(self, vendor_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.vendors.find_one({"id": vendor_id}, {"_id": 0})

    async def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.events.find_one({"id": event_id}, {"_id": 0})

    async def get_service_definition(self, vendor_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.service_definitions.find_one({"vendor_id": vendor_id}, {"_id": 0})

    async def insert_booking(self, booking_doc: Dict[str, Any], session=None) -> None:
        await self.db.bookings.insert_one(booking_doc, session=session)

    async def update_booking(self, booking_id: str, update_data: Dict[str, Any], session=None):
        return await self.db.bookings.update_one({"id": booking_id}, {"$set": update_data}, session=session)

    async def insert_booking_audit_log(
        self,
        booking_id: str,
        actor_id: str,
        actor_role: str,
        action: str,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        session=None,
    ) -> None:
        doc = {
            "id": str(datetime.now(timezone.utc).timestamp()).replace(".", ""),
            "booking_id": booking_id,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action": action,
            "reason": reason,
            "details": details or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await self.db.booking_audit_logs.insert_one(doc, session=session)

    async def increment_vendor_metrics(
        self,
        vendor_id: str,
        delta_accepted: int = 0,
        delta_rejected: int = 0,
        delta_completed: int = 0,
        delta_emergency: int = 0,
        reliability_penalty: float = 0.0,
        visibility_penalty: float = 0.0,
        session=None,
    ) -> None:
        inc: Dict[str, Any] = {}
        if delta_accepted:
            inc["accepted_count"] = delta_accepted
        if delta_rejected:
            inc["rejected_count"] = delta_rejected
        if delta_completed:
            inc["completed_count"] = delta_completed
        if delta_emergency:
            inc["emergency_count"] = delta_emergency
        if reliability_penalty:
            inc["reliability_score"] = -abs(reliability_penalty)
        if visibility_penalty:
            inc["visibility_score"] = -abs(visibility_penalty)

        if inc:
            await self.db.vendors.update_one({"id": vendor_id}, {"$inc": inc}, session=session)
            vendor = await self.db.vendors.find_one(
                {"id": vendor_id},
                {"_id": 0, "accepted_count": 1, "rejected_count": 1},
                session=session,
            )
            if vendor:
                accepted = vendor.get("accepted_count", 0) or 0
                rejected = vendor.get("rejected_count", 0) or 0
                denom = accepted + rejected
                rate = (accepted / denom) if denom > 0 else 0.0
                await self.db.vendors.update_one(
                    {"id": vendor_id}, {"$set": {"acceptance_rate": rate}}, session=session
                )

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.users.find_one({"id": user_id}, {"_id": 0})

    async def list_emergency_bookings(self, skip: int, limit: int) -> List[Dict[str, Any]]:
        cursor = (
            self.db.bookings.find({"status": "cancelled_by_vendor_emergency"}, {"_id": 0})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return await cursor.to_list(limit)

    async def list_vendors_by_ids_minimal(self, vendor_ids: List[str]) -> List[Dict[str, Any]]:
        if not vendor_ids:
            return []
        cursor = self.db.vendors.find(
            {"id": {"$in": vendor_ids}},
            {"_id": 0, "id": 1, "business_name": 1, "rating": 1},
        )
        return await cursor.to_list(len(vendor_ids))

    async def insert_platform_audit_log(
        self,
        action_type: str,
        performed_by: str,
        entity_type: str,
        entity_id: str,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        performed_by_id: Optional[str] = None,
        session=None,
    ) -> None:
        log = {
            "id": str(uuid.uuid4()),
            "action_type": action_type,
            "performed_by": performed_by,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "old_value": old_value or {},
            "new_value": new_value or {},
            "performed_by_id": performed_by_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            await self.db.audit_logs.insert_one(log, session=session)
        except Exception:
            pass

    async def create_replacement_booking_and_resolve_original(
        self,
        original_booking_id: str,
        new_booking_doc: Dict[str, Any],
        resolution_data: Dict[str, Any],
        session=None,
    ) -> None:
        await self.db.bookings.insert_one(new_booking_doc, session=session)
        await self.db.bookings.update_one(
            {"id": original_booking_id},
            {"$set": resolution_data},
            session=session,
        )

    async def with_transaction(self, fn):
        client = self.db.client
        async with await client.start_session() as session:
            async with session.start_transaction():
                return await fn(session)
