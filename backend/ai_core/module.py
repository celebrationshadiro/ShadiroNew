from __future__ import annotations

from ai_core.config import get_ai_config
from ai_core.control_plane import ControlPlane
from ai_core.decision_engine import DecisionEngine
from ai_core.drift_monitor import DriftMonitor
from ai_core.model_registry import ModelRegistry
from ai_core.profit_monitor import ProfitMonitor
from ai_core.risk_engine import RiskEngine
from app.services.decision_model_service import DecisionModelService
from app.services.decision_service import DecisionService
from app.services.feature_monitor_service import FeatureMonitorService
from app.services.profit_monitor_service import ProfitMonitorService
from app.services.risk_service import RiskService


class AIModule:
    def __init__(
        self,
        db,
        decision_service: DecisionService,
        decision_model_service: DecisionModelService,
        risk_service: RiskService,
        feature_monitor_service: FeatureMonitorService,
        profit_monitor_service: ProfitMonitorService,
    ) -> None:
        ai_config = get_ai_config()
        self.control_plane = ControlPlane(db, ai_config)
        self.decision_engine = DecisionEngine(decision_service)
        self.risk_engine = RiskEngine(risk_service)
        self.drift_monitor = DriftMonitor(feature_monitor_service)
        self.profit_monitor = ProfitMonitor(profit_monitor_service, feature_monitor_service, decision_model_service)
        self.model_registry = ModelRegistry(decision_model_service, risk_service)

