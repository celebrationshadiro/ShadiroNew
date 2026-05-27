from __future__ import annotations

from typing import Any, Dict

from app.services.feature_monitor_service import FeatureMonitorService
from app.services.decision_model_service import DecisionModelService
from app.services.profit_monitor_service import ProfitMonitorService


class ProfitMonitor:
    def __init__(
        self,
        profit_monitor_service: ProfitMonitorService,
        feature_monitor_service: FeatureMonitorService,
        decision_model_service: DecisionModelService,
    ) -> None:
        self.profit_monitor_service = profit_monitor_service
        self.feature_monitor_service = feature_monitor_service
        self.decision_model_service = decision_model_service

    async def health(self) -> Dict[str, Any]:
        health = await self.feature_monitor_service.get_ai_health(decision_model_service=self.decision_model_service)
        profit = await self.profit_monitor_service.evaluate_profitability()
        return {**health, "profitability": profit}

