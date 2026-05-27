from __future__ import annotations

import pytest

from ai_core.model_registry import ModelRegistry
from app.models.schemas import AIRollbackRequest


class _DecisionModelService:
    async def get_model_performance(self):
        return {"ok": True}

    async def calibrate_model(self, manual_override=False, triggered_by=""):
        return {"status": "ok", "triggered_by": triggered_by}

    async def rollback_to_version(self, target_version: int):
        return {"status": "ok", "active_version": target_version}


class _RiskService:
    async def rollback_to_version(self, target_version: int):
        return {"status": "ok", "active_version": target_version}


@pytest.mark.anyio
async def test_model_registry_paths():
    reg = ModelRegistry(_DecisionModelService(), _RiskService())
    perf = await reg.get_decision_performance()
    assert perf["ok"] is True

    calib = await reg.calibrate_decision_model("u1")
    assert calib["status"] == "ok"

    r1 = await reg.rollback(AIRollbackRequest(model_type="risk", target_version=2))
    r2 = await reg.rollback(AIRollbackRequest(model_type="decision", target_version=4))
    assert r1["active_version"] == 2
    assert r2["active_version"] == 4

