from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
from datetime import datetime, timezone

from auth import get_current_user, require_role
from models import UserRole

router = APIRouter(prefix="/api/disputes", tags=["disputes"])


@router.post("")
async def create_dispute(payload: Dict[str, Any], request: Request, current_user: dict = Depends(get_current_user)):
    db = request.app.state.db
    dispute = {
        "id": payload.get("id") or f"disp_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
        "booking_id": payload.get("booking_id"),
        "quote_id": payload.get("quote_id"),
        "order_id": payload.get("order_id"),
        "raised_by": current_user["sub"],
        "role": current_user.get("role"),
        "reason": payload.get("reason") or "",
        "details": payload.get("details") or "",
        "evidence": payload.get("evidence") or [],
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.disputes.insert_one(dispute)
    return dispute


@router.get("/admin")
async def list_disputes(request: Request, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    db = request.app.state.db
    cursor = db.disputes.find({}, {"_id": 0}).sort("created_at", -1).limit(200)
    items = await cursor.to_list(200)
    return {"count": len(items), "items": items}


@router.put("/admin/{dispute_id}/resolve")
async def resolve_dispute(dispute_id: str, payload: Dict[str, Any], request: Request, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    db = request.app.state.db
    result = await db.disputes.update_one(
        {"id": dispute_id},
        {"$set": {"status": payload.get("status", "resolved"), "resolution": payload.get("resolution"), "resolved_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return {"status": "ok", "id": dispute_id}
