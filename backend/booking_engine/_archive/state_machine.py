from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def transition(
    db: AsyncIOMotorDatabase,
    collection: str,
    doc_id: str,
    from_status: str,
    to_status: str,
    actor_role: str,
    actor_id: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """
    Optimistic-lock status transition with auto audit trail.

    Rules:
    - Reads current `version` from document.
    - Updates only when both `status` and `version` still match.
    - Increments `version` on every successful transition.
    - Logs transition to `state_transitions` collection.
    """
    coll = getattr(db, collection, None)
    if coll is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unknown collection: {collection}",
        )

    current = await coll.find_one({"id": doc_id}, {"_id": 0, "status": 1, "version": 1})
    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if str(current.get("status")) != str(from_status):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflict: stale state or invalid transition",
        )

    current_version = int(current.get("version", 1))
    now = utcnow()

    updated = await coll.find_one_and_update(
        {
            "id": doc_id,
            "status": from_status,
            "version": current_version,
        },
        {
            "$set": {
                "status": to_status,
                "updated_at": now,
            },
            "$inc": {"version": 1},
        },
        return_document=ReturnDocument.AFTER,
        projection={"_id": 0},
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflict: stale state or invalid transition",
        )

    await db.state_transitions.insert_one(
        {
            "entity_type": collection.upper(),
            "entity_id": doc_id,
            "from_status": from_status,
            "to_status": to_status,
            "actor_role": actor_role,
            "actor_id": actor_id,
            "reason": reason,
            "created_at": now,
        }
    )
    return updated

