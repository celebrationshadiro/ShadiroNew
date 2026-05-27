from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class AIControlService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db

    async def get_control_config(self) -> Dict[str, Any]:
        doc = await self.db.ai_control_config.find_one({"_id": "global"})
        if doc:
            return doc
        now = datetime.now(timezone.utc)
        doc = {
            "_id": "global",
            "freeze_all_models": False,
            "freeze_risk_model": False,
            "freeze_decision_model": False,
            "created_at": now,
            "updated_at": now,
        }
        await self.db.ai_control_config.insert_one(doc)
        return doc

    async def is_frozen(self, scope: str) -> bool:
        cfg = await self.get_control_config()
        if cfg.get("freeze_all_models", False):
            return True
        if scope == "risk":
            return bool(cfg.get("freeze_risk_model", False))
        if scope == "decision":
            return bool(cfg.get("freeze_decision_model", False))
        return False

    async def set_freeze(self, *, decision: bool | None = None, risk: bool | None = None, all_models: bool | None = None) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        update: Dict[str, Any] = {"updated_at": now}
        if decision is not None:
            update["freeze_decision_model"] = bool(decision)
        if risk is not None:
            update["freeze_risk_model"] = bool(risk)
        if all_models is not None:
            update["freeze_all_models"] = bool(all_models)
        await self.db.ai_control_config.update_one({"_id": "global"}, {"$set": update}, upsert=True)
        return await self.get_control_config()

    async def get_financial_control(self) -> Dict[str, Any]:
        doc = await self.db.ai_financial_control.find_one({"_id": "global"})
        if doc:
            return doc
        now = datetime.now(timezone.utc)
        doc = {
            "_id": "global",
            "max_daily_risk_exposure": 100000.0,
            "max_dispute_rate": 0.15,
            "auto_freeze_enabled": True,
            "created_at": now,
            "updated_at": now,
        }
        await self.db.ai_financial_control.insert_one(doc)
        return doc

