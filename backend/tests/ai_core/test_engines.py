from __future__ import annotations

import pytest

from ai_core.decision_engine import DecisionEngine
from ai_core.drift_monitor import DriftMonitor
from ai_core.profit_monitor import ProfitMonitor
from ai_core.risk_engine import RiskEngine


class _DecisionService:
    async def compute_book_now_score(self, payload):
        return {"score": 80}


class _WS:
    def __init__(self):
        self.sent = None

    async def broadcast(self, channel, payload):
        self.sent = (channel, payload)


class _Resp:
    def model_dump(self):
        return {"score": 80}


class _FeatureService:
    async def get_drift_status(self):
        return {"drift_alert_count_24h": 0}

    async def get_ai_health(self, decision_model_service):
        return {"health": "ok"}


class _ProfitService:
    async def evaluate_profitability(self):
        return {"last_7d_revenue": 1}


class _RiskService:
    async def rollback_to_version(self, target_version):
        return {"status": "ok", "active_version": target_version}

    async def maybe_auto_rebalance_weights(self):
        return {"status": "ok"}


@pytest.mark.anyio
async def test_decision_engine_and_broadcast():
    engine = DecisionEngine(_DecisionService())
    res = await engine.score(payload=object())
    assert res["score"] == 80
    ws = _WS()
    payload = type("P", (), {"event_id": "e1", "vendor_id": "v1"})()
    await engine.broadcast_score(ws, payload, _Resp())
    assert ws.sent[0] == "e1:v1"


@pytest.mark.anyio
async def test_risk_drift_profit_engines():
    risk = RiskEngine(_RiskService())
    drift = DriftMonitor(_FeatureService())
    profit = ProfitMonitor(_ProfitService(), _FeatureService(), object())
    assert (await risk.rollback(3))["active_version"] == 3
    assert (await risk.maybe_rebalance())["status"] == "ok"
    assert (await drift.status())["drift_alert_count_24h"] == 0
    assert "profitability" in await profit.health()

