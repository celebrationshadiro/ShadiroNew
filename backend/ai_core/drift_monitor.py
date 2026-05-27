from __future__ import annotations

from typing import Any, Dict

from app.services.feature_monitor_service import FeatureMonitorService


class DriftMonitor:
    def __init__(self, service: FeatureMonitorService) -> None:
        self.service = service

    async def status(self) -> Dict[str, Any]:
        return await self.service.get_drift_status()

