from datetime import datetime, timezone, timedelta
import pytest
from models import BookingStatus, UserRole

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

async def _seed_vendor(db, vendor_id: str, user_id: str, status: str = "APPROVED"):
    await db.vendors.insert_one(
        {
            "id": vendor_id,
            "user_id": user_id,
            "business_name": "Test Vendor",
            "category_id": "photography",
            "vendor_type": "service_vendor",
            "city": "Mumbai",
            "status": status,
            "commission_percentage": 10.0,
            "minimum_commission": 0.0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )

async def test_booking_create_flow(client, app_with_overrides):
    db = app_with_overrides["db"]
    await _seed_vendor(db, vendor_id="vendor-1", user_id="vendor-user-1")
    await db.packages.insert_one(
        {
            "id": "package-1",
            "vendor_id": "vendor-1",
            "name": "Gold Photography Package",
            "price": 15.0, # 1500 paise
            "is_active": True,
        }
    )

    payload = {
        "idempotency_key": "idempotency-key-1",
        "vendor_id": "vendor-1",
        "category_type": "service",
        "items": [
            {"item_id": "package-1", "title": "Gold Photography Package", "qty": 1}
        ],
        "total_amount_paise": 1500,
    }

    response = await client.post("/api/bookings/intent", json=payload)
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["data"]["vendor_id"] == "vendor-1"
    assert body["data"]["user_id"] == "user-1"
    assert body["data"]["status"] == "PENDING"

async def test_booking_cancel_flow(client, app_with_overrides):
    db = app_with_overrides["db"]
    await _seed_vendor(db, vendor_id="vendor-1", user_id="vendor-user-1")
    await db.bookings.insert_one(
        {
            "id": "booking-cancel-1",
            "user_id": "user-1",
            "vendor_id": "vendor-1",
            "category_type": "service",
            "status": "CONFIRMED",
            "version": 1,
            "created_at": datetime.now(timezone.utc),
            "amount_gross_paise": 90000,
            "commission_rate_bps": 1000,
            "commission_amount_paise": 9000,
            "vendor_net_paise": 81000,
            "items": [],
        }
    )

    cancel_payload = {
        "reason": "Change of plans",
        "expected_version": 1
    }

    response = await client.post("/api/bookings/booking-cancel-1/cancel", json=cancel_payload)
    assert response.status_code == 200, response.text
    assert response.json()["data"]["status"] == "CANCELLED"

    updated = await db.bookings.find_one({"id": "booking-cancel-1"}, {"_id": 0})
    assert updated["status"] == "CANCELLED"

async def test_payment_success_flow(client, app_with_overrides):
    db = app_with_overrides["db"]
    await db.users.insert_one(
        {
            "id": "user-1",
            "email": "user1@test.com",
            "name": "User One",
            "role": "user",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    await _seed_vendor(db, vendor_id="vendor-1", user_id="vendor-user-1")
    
    now = datetime.now(timezone.utc)
    await db.booking_intents.insert_one(
        {
            "id": "bint-1",
            "idempotency_key": "idempotency-key-2",
            "user_id": "user-1",
            "vendor_id": "vendor-1",
            "category_type": "service",
            "status": "PENDING",
            "total_amount_paise": 120000,
            "expires_at": now + timedelta(hours=1),
            "created_at": now,
            "items": [
                {"item_id": "package-1", "title": "Package 1", "qty": 1, "unit_price_paise": 120000, "total_price_paise": 120000}
            ],
        }
    )

    create_order_resp = await client.post("/api/bookings/bint-1/pay")
    assert create_order_resp.status_code == 200, create_order_resp.text
    create_payload = create_order_resp.json()
    assert "razorpay_order_id" in create_payload["data"]

    verify_resp = await client.post(
        "/api/bookings/verify",
        json={
            "razorpay_order_id": create_payload["data"]["razorpay_order_id"],
            "razorpay_payment_id": "pay_test_1",
            "razorpay_signature": "valid_signature",
            "booking_intent_id": "bint-1",
            "idempotency_key": "idempotency-key-3",
        },
    )
    assert verify_resp.status_code == 200, verify_resp.text
    assert verify_resp.json()["data"]["payment_status"] == "CLIENT_VERIFIED"

    payment_doc = await db.payments.find_one({"booking_intent_id": "bint-1"}, {"_id": 0})
    assert payment_doc is not None

    booking_doc = await db.bookings.find_one({"intent_id": "bint-1"}, {"_id": 0})
    assert booking_doc["status"] == "PAYMENT_RECEIVED"
    assert booking_doc.get("payment_id")

async def test_admin_vendor_approval_flow(client, app_with_overrides):
    db = app_with_overrides["db"]
    app_with_overrides["auth_state"]["user"] = {
        "sub": "admin-1",
        "role": "admin",
        "email": "admin@test.com",
    }

    await db.users.insert_one(
        {
            "id": "vendor-owner-1",
            "email": "vendor-owner@test.com",
            "name": "Vendor Owner",
            "role": "vendor",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    await _seed_vendor(db, vendor_id="vendor-approve-1", user_id="vendor-owner-1", status="pending")

    response = await client.post(
        "/api/admin/vendors/vendor-approve-1/action",
        json={"action": "approve", "reason": "Meets criteria"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["data"]["status"] == "APPROVED"

    vendor_doc = await db.vendors.find_one({"id": "vendor-approve-1"}, {"_id": 0})
    assert vendor_doc["status"] == "APPROVED"
