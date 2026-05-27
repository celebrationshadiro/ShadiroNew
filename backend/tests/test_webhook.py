import hashlib
import hmac
import json
import os
import time
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
os.environ["RAZORPAY_WEBHOOK_SECRET"] = "test_webhook_secret"

from main import app
from payments.execution_service import PaymentExecutionService


pytestmark = pytest.mark.asyncio


class FakeRazorpayClient:
    pass


@pytest_asyncio.fixture
async def db():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    database = client["shadiro_test_webhook"]
    await client.drop_database(database.name)
    await database.webhook_events.create_index("event_id", unique=True)
    yield database
    await client.drop_database(database.name)
    client.close()


@pytest_asyncio.fixture
async def client(db):
    app.state.db = db
    app.state.razorpay_client = FakeRazorpayClient()
    if hasattr(app.state, "limiter"):
        app.state.limiter.enabled = False
    from core.config import get_settings
    get_settings().RAZORPAY_WEBHOOK_SECRET = "test_webhook_secret"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


def _body(event_id="evt_1", order_id="order_test_1", amount=10000):
    return {
        "id": event_id,
        "event": "payment.captured",
        "created_at": int(time.time()),
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_rzp_1",
                    "order_id": order_id,
                    "amount": amount,
                    "currency": "INR",
                }
            }
        },
    }


def _headers(event_id, raw_body):
    signature = hmac.new(
        os.environ["RAZORPAY_WEBHOOK_SECRET"].encode("utf-8"),
        f"{event_id}{raw_body.decode('utf-8')}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        "x-razorpay-event-id": event_id,
        "x-razorpay-signature": signature,
        "content-type": "application/json",
    }


async def _seed_payment(db):
    now = datetime.now(timezone.utc)
    await db.vendors.insert_one({"id": "vendor_1", "status": "approved", "is_active": True})
    await db.booking_intents.insert_one(
        {
            "id": "intent_1",
            "user_id": "user_1",
            "vendor_id": "vendor_1",
            "category_type": "service",
            "items": [],
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
            "razorpay_order_id": "order_test_1",
            "amount_paise": 10000,
            "amount": 10000,
            "currency": "INR",
            "status": "CREATED",
        }
    )


async def _process_webhook_without_transactions(self, *, event_id, event, payload, signature, request_id, app_state=None):
    payment = await self.db.payments.find_one({"razorpay_order_id": payload["payload"]["payment"]["entity"]["order_id"]})
    intent = await self.db.booking_intents.find_one({"id": payment["booking_intent_id"]})
    booking_doc = {
        "id": "book_webhook_1",
        "intent_id": intent["id"],
        "user_id": intent["user_id"],
        "vendor_id": intent["vendor_id"],
        "status": "PAYMENT_RECEIVED",
        "payment_id": payment["id"],
        "amount_gross_paise": intent["total_amount_paise"],
        "vendor_net_paise": 9000,
        "resource_lock_ids": [],
        "created_at": datetime.now(timezone.utc),
    }
    await self.db.bookings.insert_one(booking_doc)
    await self.db.payments.update_one({"id": payment["id"]}, {"$set": {"status": "CONFIRMED", "booking_id": booking_doc["id"]}})
    return {"processed": True, "booking_id": booking_doc["id"], "payment_status": "CONFIRMED", "booking_status": "PAYMENT_RECEIVED"}


async def test_webhook_valid_signature(client, db):
    await _seed_payment(db)
    raw = json.dumps(_body("evt_valid"), separators=(",", ":")).encode("utf-8")
    with patch.object(PaymentExecutionService, "process_payment_captured_webhook", _process_webhook_without_transactions):
        response = await client.post("/api/bookings/webhook", content=raw, headers=_headers("evt_valid", raw))

    assert response.status_code == 200, response.text
    assert response.json()["data"]["processed"] is True


async def test_webhook_invalid_signature(client, db):
    await _seed_payment(db)
    raw = json.dumps(_body("evt_bad_sig"), separators=(",", ":")).encode("utf-8")
    headers = _headers("evt_bad_sig", raw)
    tampered = json.dumps(_body("evt_bad_sig", amount=9999), separators=(",", ":")).encode("utf-8")

    response = await client.post("/api/bookings/webhook", content=tampered, headers=headers)

    assert response.status_code == 401


async def test_webhook_missing_event_id(client, db):
    body = _body("evt_missing")
    body.pop("id")
    raw = json.dumps(body, separators=(",", ":")).encode("utf-8")

    response = await client.post("/api/bookings/webhook", content=raw, headers=_headers("evt_missing", raw))

    assert response.status_code == 400


async def test_webhook_duplicate_event_id(client, db):
    await _seed_payment(db)
    raw = json.dumps(_body("evt_dupe"), separators=(",", ":")).encode("utf-8")
    headers = _headers("evt_dupe", raw)
    with patch.object(PaymentExecutionService, "process_payment_captured_webhook", _process_webhook_without_transactions):
        first = await client.post("/api/bookings/webhook", content=raw, headers=headers)
        second = await client.post("/api/bookings/webhook", content=raw, headers=headers)

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert second.json()["data"]["reason"] == "duplicate_event"


async def test_webhook_payment_captured(client, db):
    await _seed_payment(db)
    raw = json.dumps(_body("evt_booking"), separators=(",", ":")).encode("utf-8")
    with patch.object(PaymentExecutionService, "process_payment_captured_webhook", _process_webhook_without_transactions):
        response = await client.post("/api/bookings/webhook", content=raw, headers=_headers("evt_booking", raw))

    assert response.status_code == 200, response.text
    booking = await db.bookings.find_one({"intent_id": "intent_1"}, {"_id": 0})
    assert booking is not None
    assert booking["status"] == "PAYMENT_RECEIVED"
