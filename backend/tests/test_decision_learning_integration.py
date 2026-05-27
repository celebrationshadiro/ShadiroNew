from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from bson import ObjectId
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

pytest.importorskip("pydantic_settings")

from app.core.dependencies import get_decision_model_service
from app.core.security import get_current_user
from app.models.indexes import ensure_indexes
from app.routes.decision import router as decision_router
from app.services.decision_model_service import DecisionModelService
from app.services.decision_outcome_service import DecisionOutcomeService
from app.services.vendor_analytics_service import VendorAnalyticsService


@pytest.fixture
async def test_db():
    mongo_url = os.getenv("TEST_MONGO_URL", "mongodb://127.0.0.1:27017")
    db_name = f"decision_os_learning_{uuid.uuid4().hex}"
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    await client.drop_database(db_name)
    await ensure_indexes(db, settings=type("S", (), {})())
    try:
        yield db
    finally:
        await client.drop_database(db_name)
        client.close()


def _seed_outcomes(count: int, model_version: int = 1):
    now = datetime.now(timezone.utc)
    rows = []
    for i in range(count):
        success = (i % 5) != 0
        rows.append(
            {
                "_id": ObjectId(),
                "decision_id": ObjectId(),
                "booking_id": ObjectId(),
                "event_id": ObjectId(),
                "vendor_id": ObjectId(),
                "actual_booking_result": success,
                "actual_completion_status": "completed",
                "actual_dispute_flag": False if success else True,
                "actual_final_price": 1000 + i,
                "model_version": model_version,
                "predicted_booking_result": success,
                "predicted_dispute_flag": not success,
                "predicted_features": {
                    "price_fairness": 0.84 if success else 0.35,
                    "availability_confidence": 0.82 if success else 0.30,
                    "trust_score": 0.80 if success else 0.28,
                    "demand_pressure": 0.64 if success else 0.54,
                    "negotiation_probability": 0.62 if success else 0.42,
                },
                "accuracy_metrics": {"score_error": 5.0 if success else 20.0},
                "created_at": now - timedelta(minutes=i),
            }
        )
    return rows


@pytest.mark.anyio
async def test_decision_outcome_capture(test_db):
    from app.services.profit_monitor_service import ProfitMonitorService
    vendor_analytics_service = VendorAnalyticsService(test_db)
    profit_monitor_service = ProfitMonitorService(test_db)
    outcome_service = DecisionOutcomeService(test_db, vendor_analytics_service, profit_monitor_service)

    booking_id = ObjectId()
    event_id = ObjectId()
    vendor_id = ObjectId()
    await test_db.bookings.insert_one(
        {
            "_id": booking_id,
            "event_id": event_id,
            "vendor_id": vendor_id,
            "status": "completed",
            "total_amount": 2200.0,
            "currency": "USD",
            "created_at": datetime.now(timezone.utc),
        }
    )
    await test_db.decision_scores.insert_one(
        {
            "_id": ObjectId(),
            "event_id": event_id,
            "vendor_id": vendor_id,
            "score": 82,
            "recommendation": "book_now",
            "components": {
                "price_fairness": 83,
                "availability_confidence": 90,
                "trust_score": 80,
                "demand_pressure": 65,
                "negotiation_probability": 60,
            },
            "model_version": 1,
            "quoted_price": 2300.0,
            "created_at": datetime.now(timezone.utc),
        }
    )
    await test_db.escrow_transactions.insert_one(
        {
            "_id": ObjectId(),
            "booking_id": booking_id,
            "vendor_id": vendor_id,
            "tx_type": "release",
            "amount": 2200.0,
            "status": "succeeded",
            "created_at": datetime.now(timezone.utc),
        }
    )

    result = await outcome_service.record_booking_outcome(booking_id=booking_id, category="catering")
    assert result["status"] == "ok"
    outcome = await test_db.decision_outcomes.find_one({"booking_id": booking_id})
    assert outcome is not None
    assert outcome["actual_completion_status"] == "completed"
    assert "accuracy_metrics" in outcome


@pytest.mark.anyio
async def test_model_version_rollover(test_db):
    service = DecisionModelService(test_db)
    await service.ensure_active_model()
    await test_db.decision_outcomes.insert_many(_seed_outcomes(1200, model_version=1))

    result = await service.calibrate_model(manual_override=True, triggered_by="test_admin")
    assert result["status"] == "ok"
    active = await service.get_active_model()
    assert active["model_version"] == 2
    audit = await test_db.calibration_audit_logs.find_one({"model_version_to": 2})
    assert audit is not None
    assert audit["aborted_flag"] is False


@pytest.mark.anyio
async def test_calibration_abort_case(test_db, monkeypatch):
    service = DecisionModelService(test_db)
    await service.ensure_active_model()
    await test_db.decision_outcomes.insert_many(_seed_outcomes(1200, model_version=1))

    call_state = {"count": 0}

    def _fake_eval(rows, weights):
        call_state["count"] += 1
        return 0.90 if call_state["count"] == 1 else 0.80

    monkeypatch.setattr(service, "_evaluate_booking_accuracy", _fake_eval)
    result = await service.calibrate_model(manual_override=True, triggered_by="test_admin")
    assert result["status"] == "aborted"
    assert result["reason"] == "booking_accuracy_regression_gt_5pct"
    active = await service.get_active_model()
    assert active["model_version"] == 1


@pytest.mark.anyio
async def test_manual_calibration_endpoint_success(test_db):
    service = DecisionModelService(test_db)
    await service.ensure_active_model()
    await test_db.decision_outcomes.insert_many(_seed_outcomes(1200, model_version=1))

    from app.core.dependencies import guard_ai_route

    app = FastAPI()
    app.state.db = test_db
    app.include_router(decision_router, prefix="/api/v1")
    app.dependency_overrides[get_decision_model_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: {"sub": "admin-user", "role": "admin"}
    app.dependency_overrides[guard_ai_route] = lambda: {"sub": "admin-user", "role": "admin"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/decision/model/calibrate")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["model_version_to"] == 2


@pytest.mark.anyio
async def test_freeze_behavior(test_db):
    service = DecisionModelService(test_db)
    active = await service.ensure_active_model()
    await test_db.decision_model_config.update_one({"_id": active["_id"]}, {"$set": {"frozen": True}})
    await test_db.decision_outcomes.insert_many(_seed_outcomes(1200, model_version=1))

    auto_result = await service.calibrate_model(manual_override=False, triggered_by="auto")
    assert auto_result["status"] == "skipped"
    assert auto_result["reason"] == "model_frozen"

    manual_result = await service.calibrate_model(manual_override=True, triggered_by="admin_override")
    assert manual_result["status"] == "ok"
    active_model = await service.get_active_model()
    assert active_model["model_version"] == 2
