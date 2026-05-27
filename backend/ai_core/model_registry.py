from __future__ import annotations

from typing import Any, Dict

from app.models.schemas import AIRollbackRequest
from app.services.decision_model_service import DecisionModelService
from app.services.risk_service import RiskService


class ModelRegistry:
    def __init__(self, decision_model_service: DecisionModelService, risk_service: RiskService) -> None:
        self.decision_model_service = decision_model_service
        self.risk_service = risk_service

    async def get_decision_performance(self) -> Dict[str, Any]:
        return await self.decision_model_service.get_model_performance()

    async def calibrate_decision_model(self, actor: str) -> Dict[str, Any]:
        return await self.decision_model_service.calibrate_model(manual_override=True, triggered_by=f"admin:{actor}")

    async def rollback(self, payload: AIRollbackRequest) -> Dict[str, Any]:
        if payload.model_type == "risk":
            return await self.risk_service.rollback_to_version(payload.target_version)
        return await self.decision_model_service.rollback_to_version(payload.target_version)

