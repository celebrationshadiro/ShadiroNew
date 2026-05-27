from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from passlib.context import CryptContext
from pymongo import MongoClient


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def days_from_now(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).date().isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def ensure_user(db, email: str, name: str, role: str = "user", phone: str | None = None) -> dict:
    existing = db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        return existing
    doc = {
        "id": str(uuid.uuid4()),
        "email": email,
        "name": name,
        "phone": phone,
        "role": role,
        "hashed_password": pwd_context.hash("Test@12345"),
        "created_at": now_iso(),
        "is_active": True,
    }
    db.users.insert_one(doc)
    return doc


def main() -> None:
    load_dotenv("backend/.env")
    mongo_url = os.getenv("MONGO_URL")
    db_name = os.getenv("DB_NAME")
    if not mongo_url or not db_name:
        raise RuntimeError("Missing MONGO_URL or DB_NAME in backend/.env")

    client = MongoClient(mongo_url)
    db = client[db_name]

    vendors = list(
        db.vendors.find(
            {"category_id": {"$regex": "^cat-"}},
            {"_id": 0, "id": 1, "user_id": 1, "business_name": 1, "category_id": 1, "city": 1},
        )
    )
    if not vendors:
        raise RuntimeError("No vendors found. Create vendor records before running flow seed.")

    users = [
        ensure_user(db, "customer1@test.com", "Aditi Sharma", "user", "9100000001"),
        ensure_user(db, "customer2@test.com", "Rahul Mehta", "user", "9100000002"),
        ensure_user(db, "customer3@test.com", "Nisha Verma", "user", "9100000003"),
    ]

    events_created = 0
    bookings_created = 0
    quotes_created = 0
    orders_created = 0
    payments_created = 0
    ledger_created = 0

    for i, vendor in enumerate(vendors):
        customer = users[i % len(users)]
        amount = 25000 + (i * 5000)
        commission = round(amount * 0.10, 2)
        gateway_fee = round(amount * 0.02, 2)
        net = round(amount - commission - gateway_fee, 2)

        event_id = make_id("evt")
        event_doc = {
            "id": event_id,
            "user_id": customer["id"],
            "title": f"Wedding Function {i + 1}",
            "event_type": "wedding",
            "event_date": days_from_now(20 + i),
            "city": vendor.get("city") or "Patna",
            "guest_count": 150 + i * 20,
            "created_at": now_iso(),
        }
        db.events.update_one({"id": event_id}, {"$set": event_doc}, upsert=True)
        events_created += 1

        quote_id = make_id("q")
        quote_doc = {
            "id": quote_id,
            "user_id": customer["id"],
            "vendor_id": vendor["id"],
            "event_id": event_id,
            "requested_services": ["Standard package"],
            "status": "pending",
            "message": "Please share best quote.",
            "lead_score": 72,
            "lead_score_label": "Warm",
            "created_at": now_iso(),
        }
        db.quotes.update_one({"id": quote_id}, {"$set": quote_doc}, upsert=True)
        quotes_created += 1

        booking_id = make_id("bk")
        booking_status = "confirmed" if i % 3 != 0 else "pending"
        booking_doc = {
            "id": booking_id,
            "user_id": customer["id"],
            "user_name": customer["name"],
            "vendor_id": vendor["id"],
            "vendor_user_id": vendor["user_id"],
            "event_id": event_id,
            "event_date": event_doc["event_date"],
            "event_time": "18:00",
            "city": event_doc["city"],
            "address": "Boring Road, Patna",
            "status": booking_status,
            "total_amount": amount,
            "currency": "INR",
            "created_at": now_iso(),
        }
        db.bookings.update_one({"id": booking_id}, {"$set": booking_doc}, upsert=True)
        bookings_created += 1

        order_id = make_id("ord")
        order_status = "confirmed" if booking_status == "confirmed" else "pending"
        order_doc = {
            "id": order_id,
            "booking_id": booking_id,
            "user_id": customer["id"],
            "vendor_id": vendor["id"],
            "status": order_status,
            "total_amount": amount,
            "created_at": now_iso(),
        }
        db.orders.update_one({"id": order_id}, {"$set": order_doc}, upsert=True)
        orders_created += 1

        payment_id = make_id("pay")
        razorpay_order_id = f"order_{uuid.uuid4().hex[:10]}"
        razorpay_payment_id = f"pay_{uuid.uuid4().hex[:10]}"
        payment_status = "success" if booking_status == "confirmed" else "pending"
        payment_doc = {
            "id": payment_id,
            "order_id": order_id,
            "booking_id": booking_id,
            "user_id": customer["id"],
            "vendor_id": vendor["id"],
            "amount": amount,
            "currency": "INR",
            "status": payment_status,
            "provider": "razorpay",
            "razorpay_order_id": razorpay_order_id,
            # Keep non-null unique value to satisfy uniq_payments_razorpay_payment_id index.
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": "test_signature",
            "created_at": now_iso(),
        }
        db.payments.update_one({"id": payment_id}, {"$set": payment_doc}, upsert=True)
        payments_created += 1

        if payment_status == "success":
            ledger_doc = {
                "id": make_id("led"),
                "vendor_id": vendor["id"],
                "reference_id": order_id,
                "booking_id": booking_id,
                "gross_amount": amount,
                "commission_amount": commission,
                "gateway_fee": gateway_fee,
                "net_amount": net,
                "created_at": now_iso(),
            }
            db.vendor_ledger.update_one(
                {"reference_id": order_id},
                {"$set": ledger_doc},
                upsert=True,
            )
            db.vendors.update_one(
                {"id": vendor["id"]},
                {
                    "$set": {"updated_at": now_iso()},
                    "$inc": {"vendor_payout_balance": net},
                },
            )
            ledger_created += 1

    print("Flow seed complete")
    print(f"Events upserted: {events_created}")
    print(f"Quotes upserted: {quotes_created}")
    print(f"Bookings upserted: {bookings_created}")
    print(f"Orders upserted: {orders_created}")
    print(f"Payments upserted: {payments_created}")
    print(f"Vendor ledger upserted: {ledger_created}")
    print("Customer logins (password: Test@12345):")
    for u in users:
        print(f"- {u['email']}")


if __name__ == "__main__":
    main()
