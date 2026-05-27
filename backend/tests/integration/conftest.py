import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

# Ensure backend imports work when tests are executed from repo root.
BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from api.deps import get_db, get_razorpay_client
from auth import get_current_user
from models import UserRole
from modules.bookings.repository import BookingRepository
from server import app
from tests.integration.test_config import get_test_config


class _FakeRazorpayOrder:
    def __init__(self):
        self.calls = 0

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.calls += 1
        return {
            "id": f"order_test_{self.calls}",
            "amount": payload["amount"],
            "currency": payload["currency"],
        }


class _FakeRazorpayUtility:
    def verify_payment_signature(self, params: Dict[str, Any]) -> None:
        if params.get("razorpay_signature") != "valid_signature":
            raise ValueError("invalid signature")


class FakeRazorpayClient:
    def __init__(self):
        self.order = _FakeRazorpayOrder()
        self.utility = _FakeRazorpayUtility()


@pytest.fixture
async def mongo_client() -> AsyncIOMotorClient:
    cfg = get_test_config()
    client = AsyncIOMotorClient(cfg.mongo_url)
    yield client
    client.close()


@pytest.fixture
async def test_db(mongo_client: AsyncIOMotorClient):
    cfg = get_test_config()
    db = mongo_client[cfg.db_name]
    await mongo_client.drop_database(cfg.db_name)
    yield db
    await mongo_client.drop_database(cfg.db_name)


@pytest.fixture
async def app_with_overrides(test_db, monkeypatch):
    auth_state = {
        "user": {
            "id": "user-1",
            "sub": "user-1",
            "role": "customer",
            "email": "user1@test.com"
        }
    }
    fake_razorpay = FakeRazorpayClient()

    async def _override_get_db():
        return test_db

    async def _override_get_current_user():
        return auth_state["user"]

    async def _override_require_admin():
        return auth_state["user"]

    def _override_get_razorpay_client():
        return fake_razorpay

    async def _noop_email(*args, **kwargs):
        return None

    async def _insert_booking_without_mutation(self, booking_doc, session=None):
        # pymongo mutates dict with _id; keep API responses stable in tests.
        await self.db.bookings.insert_one(dict(booking_doc), session=session)

    async def _fallback_with_transaction(self, fn):
        # Local Mongo setups are often standalone and don't support sessions.
        return await fn(None)

    class FakeTransaction:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeSession:
        def __init__(self):
            self.in_transaction = False
            self._pinned_address = None
            self._pinned_connection = None
            self.has_ended = False
            self._client = test_db.client

        def start_transaction(self):
            self.in_transaction = True
            return FakeTransaction()

        def _txn_read_preference(self):
            return None

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            self.in_transaction = False
            return False

    async def _fake_start_session(*args, **kwargs):
        return FakeSession()

    monkeypatch.setattr(test_db.client, "start_session", _fake_start_session, raising=False)

    app.state.db = test_db
    app.state.razorpay_client = fake_razorpay

    from core.security import get_current_user as core_get_current_user, require_admin as core_require_admin
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[core_get_current_user] = _override_get_current_user
    app.dependency_overrides[core_require_admin] = _override_require_admin
    app.dependency_overrides[get_razorpay_client] = _override_get_razorpay_client

    # Module-level imported email functions
    monkeypatch.setattr("modules.payments.service.send_booking_confirmation_email", _noop_email, raising=False)
    monkeypatch.setattr("modules.admin.service.send_vendor_approval_email", _noop_email, raising=False)
    monkeypatch.setattr("modules.admin.service.send_vendor_rejection_email", _noop_email, raising=False)

    # Functions imported lazily from email_service inside service methods
    monkeypatch.setattr("email_service.send_vendor_new_quote_request", _noop_email, raising=False)
    monkeypatch.setattr("email_service.send_booking_cancelled_email", _noop_email, raising=False)
    monkeypatch.setattr("email_service.send_refund_initiated_email", _noop_email, raising=False)
    monkeypatch.setattr("email_service.send_emergency_escalation_email", _noop_email, raising=False)
    monkeypatch.setattr("email_service.send_emergency_admin_alert", _noop_email, raising=False)
    monkeypatch.setattr("email_service.send_vendor_emergency_cancelled_email", _noop_email, raising=False)
    monkeypatch.setattr(BookingRepository, "insert_booking", _insert_booking_without_mutation, raising=True)
    monkeypatch.setattr(BookingRepository, "with_transaction", _fallback_with_transaction, raising=True)

    yield {"app": app, "auth_state": auth_state, "razorpay": fake_razorpay, "db": test_db}

    app.dependency_overrides.clear()


@pytest.fixture
async def client(app_with_overrides):
    transport = ASGITransport(app=app_with_overrides["app"])
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client
