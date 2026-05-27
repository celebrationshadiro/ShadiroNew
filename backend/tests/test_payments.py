import os
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "shadiro_test")
os.environ.setdefault("JWT_SECRET_KEY", "1234567890123456789012345678901234567890")
os.environ.setdefault("RAZORPAY_KEY_ID", "rzp_test_key")
os.environ.setdefault("RAZORPAY_KEY_SECRET", "rzp_test_secret")
os.environ.setdefault("RAZORPAY_WEBHOOK_SECRET", "test_webhook_secret")

from main import app
from routers import bookings, payments


pytestmark = pytest.mark.asyncio


class FakeRazorpayOrder:
    def create(self, payload):
        return {
            "id": "order_test_1",
            "amount": payload["amount"],
            "currency": payload["currency"],
        }


class FakeRazorpayUtility:
    def verify_payment_signature(self, payload):
        return None


class FakeRazorpayClient:
    def __init__(self):
        self.order = FakeRazorpayOrder()
        self.utility = FakeRazorpayUtility()


@pytest_asyncio.fixture
async def db():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    database = client["shadiro_test_payments"]
    await client.drop_database(database.name)
    yield database
    await client.drop_database(database.name)
    client.close()


@pytest_asyncio.fixture
async def client(db):
    fake_razorpay = FakeRazorpayClient()

    async def current_user():
        return {"id": "user_1", "role": "customer", "email": "user@test.com"}

    app.state.db = db
    app.state.razorpay_client = fake_razorpay
    if hasattr(app.state, "limiter"):
        app.state.limiter.enabled = False
    app.dependency_overrides[bookings.get_current_user] = current_user
    app.dependency_overrides[payments.get_current_user] = current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client, fake_razorpay

    app.dependency_overrides.clear()


async def _seed_vendor_intent_and_payment(db, *, payment_status="CREATED", idempotency_key=None):
    now = datetime.now(timezone.utc)
    await db.vendors.insert_one(
        {
            "id": "vendor_1",
            "user_id": "vendor_user_1",
            "status": "approved",
            "is_active": True,
            "commission_override_bps": 1000,
            "created_at": now,
        }
    )
    await db.booking_intents.insert_one(
        {
            "id": "intent_1",
            "idempotency_key": "intent_idem_1",
            "user_id": "user_1",
            "vendor_id": "vendor_1",
            "category_type": "service",
            "items": [{"item_id": "pkg_1", "title": "Package", "qty": 1}],
            "total_amount_paise": 10000,
            "status": "PENDING",
            "created_at": now,
            "updated_at": now,
        }
    )
    await db.payments.insert_one(
        {
            "id": "pay_1",
            "booking_intent_id": "intent_1",
            "amount": 10000,
            "currency": "INR",
            "status": payment_status,
            "razorpay_order_id": "order_test_1",
            "razorpay_payment_id": None,
            "razorpay_signature": None,
            "idempotency_key": idempotency_key,
            "created_at": now,
            "updated_at": now,
        }
    )


async def test_create_razorpay_order(client, db):
    async_client, fake_razorpay = client
    await _seed_vendor_intent_and_payment(db)
    await db.payments.delete_many({})

    with patch.object(fake_razorpay.order, "create", wraps=fake_razorpay.order.create) as create_order:
        response = await async_client.post("/api/bookings/intent_1/pay")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data"]["razorpay_order_id"] == "order_test_1"
    create_order.assert_called_once()


async def test_payment_verify_idempotency(client, db):
    async_client, fake_razorpay = client
    await _seed_vendor_intent_and_payment(db)
    payload = {
        "razorpay_order_id": "order_test_1",
        "razorpay_payment_id": "pay_rzp_1",
        "razorpay_signature": "valid_signature",
        "idempotency_key": "verify_idem_1",
        "booking_intent_id": "intent_1",
    }

    with patch.object(fake_razorpay.utility, "verify_payment_signature", wraps=fake_razorpay.utility.verify_payment_signature):
        first = await async_client.post("/api/bookings/verify", json=payload)
        second = await async_client.post("/api/bookings/verify", json=payload)

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert second.json()["data"]["already_processed"] is True


async def test_payment_verify_missing_idempotency(client, db):
    async_client, _ = client
    await _seed_vendor_intent_and_payment(db)
    response = await async_client.post(
        "/api/bookings/verify",
        json={
            "razorpay_order_id": "order_test_1",
            "razorpay_payment_id": "pay_rzp_1",
            "razorpay_signature": "valid_signature",
            "booking_intent_id": "intent_1",
        },
    )

    assert response.status_code == 422


async def test_payment_status(client, db):
    async_client, _ = client
    await db.bookings.insert_one({"id": "book_1", "user_id": "user_1", "payment_id": "pay_1", "status": "PAYMENT_RECEIVED"})
    await db.payments.insert_one({"id": "pay_1", "booking_id": "book_1", "status": "CONFIRMED"})

    response = await async_client.get("/api/bookings/book_1/payment/status")

    assert response.status_code == 200, response.text
    assert response.json()["data"]["status"] == "CONFIRMED"
