from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any

from auth import require_role
from models import UserRole
from services.automation_engine import normalize_schedule

router = APIRouter(prefix="/api/automation", tags=["automation"])


@router.post("/schedules")
async def create_schedule(payload: Dict[str, Any], request: Request, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    db = request.app.state.db
    try:
        schedule = normalize_schedule(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not schedule.get("id"):
        schedule["id"] = f"auto_{schedule['run_at'].replace(':', '').replace('-', '')}"

    await db.automation_schedules.insert_one(schedule)
    return schedule


@router.get("/queue")
async def get_queue(request: Request, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    db = request.app.state.db
    cursor = db.automation_schedules.find({}, {"_id": 0}).sort("run_at", 1).limit(200)
    schedules = await cursor.to_list(200)
    return {"count": len(schedules), "items": schedules}
