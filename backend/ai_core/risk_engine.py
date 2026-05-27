from __future__ import annotations

from typing import Any, Dict

from app.services.risk_service import RiskService


class RiskEngine:
    def __init__(self, service: RiskService) -> None:
        self.service = service

    async def rollback(self, target_version: int) -> Dict[str, Any]:
        return await self.service.rollback_to_version(target_version)

    async def maybe_rebalance(self) -> Dict[str, Any]:
        return await self.service.maybe_auto_rebalance_weights()

