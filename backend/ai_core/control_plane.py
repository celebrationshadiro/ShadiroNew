from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from bson import ObjectId
from fastapi import HTTPException, Request, status
from pymongo import ReturnDocument

from ai_core.config import AIConfig
from app.services.ai_control_service import AIControlService


class ControlPlane:
    def __init__(self, db, config: AIConfig) -> None:
        self.db = db
        self.config = config
        self.ai_control_service = AIControlService(db)

    async def verify_api_key(self, api_key: str | None) -> None:
        if not api_key or api_key != self.config.ai_api_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid AI API key")

    async def enforce_rate_limit(self, principal: str) -> None:
        now = datetime.now(timezone.utc)
        window = now.replace(second=0, microsecond=0)
        key = f"{principal}:{window.isoformat()}"
        doc = await self.db.ai_rate_limits.find_one_and_update(
            {"_id": key},
            {
                "$inc": {"count": 1},
                "$set": {"principal": principal, "window_start": window, "expires_at": now + timedelta(seconds=self.config.ai_rate_limit_ttl_seconds)},
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        if int(doc.get("count", 0)) > int(self.config.ai_rate_limit_per_minute):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="AI rate limit exceeded")

    async def guard_request(self, request: Request, api_key: str | None) -> Dict[str, Any]:
        await self.verify_api_key(api_key)
        principal = request.client.host if request.client else "unknown"
        await self.enforce_rate_limit(principal)
        return {"principal": principal}

    @staticmethod
    def require_admin(user: Dict[str, Any]) -> None:
        if str(user.get("role", "")).lower() != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    async def rollback_log(self, *, model_type: str, target_version: int, actor: str | None) -> None:
        await self.db.ai_rollback_logs.insert_one(
            {
                "_id": ObjectId(),
                "model_type": model_type,
                "target_version": target_version,
                "actor": actor,
                "timestamp": datetime.now(timezone.utc),
            }
        )
