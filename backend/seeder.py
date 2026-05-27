import asyncio
import os
import random
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from faker import Faker
from passlib.context import CryptContext

# Initialize Indian Faker
fake = Faker('en_IN')
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MONGO_URL = os.getenv("MONGO_URL", "mongodb://admin:password@localhost:27017/?authSource=admin")
DB_NAME = os.getenv("DB_NAME", "shadiro_db")

async def generate_dummy_data():
    print("🚀 Starting Production-Grade Data Seeding for Shadiro...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🧹 Cleaning existing test state...")
    await db.users.delete_many({})
    await db.services.delete_many({})
    await db.bookings.delete_many({})
    await db.reviews.delete_many({})
    await db.chats.delete_many({})
    await db.analytics.delete_many({})
    await db.coupons.delete_many({})
    await db.support_tickets.delete_many({})
    await db.refunds.delete_many({})

    print("⚡ PHASE E: Auto-Fixing Database Performance (Applying Indexes)...")
    await db.users.create_index("email", unique=True)
    await db.users.create_index("role")
    await db.services.create_index("vendor_id")
    await db.services.create_index([("category", 1), ("price", -1)]) # Compound index for faster filtering
    await db.bookings.create_index("customer_id")
    await db.bookings.create_index("vendor_id")
    await db.bookings.create_index("status")
    await db.bookings.create_index("created_at")
    await db.reviews.create_index("service_id")
    await db.analytics.create_index("date")
    await db.coupons.create_index("code", unique=True)
    await db.support_tickets.create_index("status")
    
    hashed_password = pwd_context.hash("Test@1234")

    # ==========================================
    # 1. CREATE TEST ACCOUNTS (PHASE 3)
    # ==========================================
    test_accounts = [
        {"name": "Super Admin", "email": "superadmin@shadiro.com", "role": "superadmin"},
        {"name": "Admin User", "email": "admin@shadiro.com", "role": "admin"},
        {"name": "Support Moderator", "email": "mod@shadiro.com", "role": "moderator"},
        {"name": "Ravi Sharma", "email": "vendor@shadiro.com", "role": "vendor"},
        {"name": "Priya Patel", "email": "customer@shadiro.com", "role": "customer"}
    ]

    for acc in test_accounts:
        acc.update({
            "password": hashed_password,
            "phone": fake.phone_number(),
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow()
        })
    
    result = await db.users.insert_many(test_accounts)
    print(f"✅ Generated {len(result.inserted_ids)} static test accounts (Password: Test@1234)")

    # ==========================================
    # 2. GENERATE REALISTIC INDIAN VENDORS
    # ==========================================
    vendor_docs = []
    for _ in range(100):
        vendor_docs.append({
            "name": fake.name(),
            "email": fake.company_email(),
            "password": hashed_password,
            "phone": fake.phone_number(),
            "role": "vendor",
            "business_name": f"{fake.first_name()} {random.choice(['Events', 'Weddings', 'Catering', 'Photography', 'Decorators'])}",
            "address": {
                "street": fake.street_address(),
                "city": fake.city_name(),
                "state": fake.state(),
                "pincode": fake.postcode()
            },
            "is_verified": random.choices([True, False], weights=[80, 20])[0],
            "rating": round(random.uniform(3.5, 5.0), 1),
            "total_earnings": 0, # Will be aggregated
            "created_at": fake.date_time_between(start_date='-365d', end_date='now')
        })
    vendors = await db.users.insert_many(vendor_docs)
    print(f"✅ Generated {len(vendors.inserted_ids)} Indian Vendors.")

    # ==========================================
    # 3. GENERATE VENDOR SERVICES & PACKAGES
    # ==========================================
    service_docs = []
    categories = ["Photography", "Catering", "Venue", "Decoration", "Makeup", "Entertainment", "Mehendi"]
    for v_id in vendors.inserted_ids:
        for _ in range(random.randint(2, 6)):
            service_docs.append({
                "vendor_id": v_id,
                "title": f"Premium {random.choice(['Wedding', 'Pre-wedding', 'Reception'])} Package",
                "category": random.choice(categories),
                "description": fake.text(max_nb_chars=200),
                "price": random.randint(10000, 1500000),
                "currency": "INR",
                "rating": round(random.uniform(3.5, 5.0), 1),
                "reviews_count": random.randint(0, 150),
                "images": [f"https://res.cloudinary.com/demo/image/upload/v1/event_{random.randint(1,10)}.jpg" for _ in range(3)],
                "created_at": fake.date_time_between(start_date='-365d', end_date='now')
            })
    services = await db.services.insert_many(service_docs)
    print(f"✅ Generated {len(services.inserted_ids)} Services/Packages.")

    # ==========================================
    # 4. GENERATE CUSTOMERS & REALISTIC BOOKINGS
    # ==========================================
    customer_docs = []
    for _ in range(500):
        customer_docs.append({
            "name": fake.name(),
            "email": fake.email(),
            "password": hashed_password,
            "phone": fake.phone_number(),
            "role": "customer",
            "created_at": fake.date_time_between(start_date='-365d', end_date='now')
        })
    customers = await db.users.insert_many(customer_docs)
    print(f"✅ Generated {len(customers.inserted_ids)} Indian Customers.")

    # ==========================================
    # 4.5 GENERATE COUPONS & OFFERS
    # ==========================================
    coupon_docs = [
        {"code": "SHADIRO50", "discount_type": "percentage", "value": 10, "max_discount": 5000, "valid_until": datetime.utcnow() + timedelta(days=90), "is_active": True},
        {"code": "FESTIVE2026", "discount_type": "flat", "value": 2000, "max_discount": 2000, "valid_until": datetime.utcnow() + timedelta(days=30), "is_active": True},
        {"code": "EARLYBIRD", "discount_type": "percentage", "value": 15, "max_discount": 10000, "valid_until": datetime.utcnow() - timedelta(days=1), "is_active": False}
    ]
    await db.coupons.insert_many(coupon_docs)
    print("✅ Generated Marketing Coupons.")

    # ==========================================
    # 5. GENERATE BOOKINGS, REVIEWS, REFUNDS & TICKETS
    # ==========================================
    booking_docs = []
    review_docs = []
    chat_docs = []
    refund_docs = []
    ticket_docs = []
    analytics_data = {}

    statuses = ["pending", "confirmed", "completed", "completed", "completed", "cancelled"]
    for _ in range(1200):
        customer_id = random.choice(customers.inserted_ids)
        service = random.choice(service_docs)
        event_date = fake.date_time_between(start_date='-300d', end_date='+90d')
        created_date = event_date - timedelta(days=random.randint(5, 60))
        status = random.choice(statuses)
        
        booking_docs.append({
            "customer_id": customer_id,
            "vendor_id": service["vendor_id"],
            "service_id": services.inserted_ids[service_docs.index(service)],
            "event_date": event_date,
            "status": status,
            "total_amount": service["price"],
            "payment_status": "paid" if status in ["confirmed", "completed"] else "pending",
            "razorpay_order_id": f"order_{fake.pystr(min_chars=14, max_chars=14)}",
            "created_at": created_date
        })

        # Generate Analytics for Admin Dashboard
        day_str = created_date.strftime("%Y-%m-%d")
        if day_str not in analytics_data:
            analytics_data[day_str] = {"revenue": 0, "bookings": 0}
        analytics_data[day_str]["bookings"] += 1
        if status in ["confirmed", "completed"]:
            analytics_data[day_str]["revenue"] += service["price"]

        # Generate Reviews for completed bookings
        if status == "completed" and random.random() > 0.3:
            review_docs.append({
                "customer_id": customer_id,
                "service_id": services.inserted_ids[service_docs.index(service)],
                "vendor_id": service["vendor_id"],
                "rating": random.randint(3, 5),
                "comment": fake.sentence(),
                "created_at": event_date + timedelta(days=random.randint(1, 10))
            })
            
        # Generate Refunds for specific cancellations
        if status == "cancelled" and random.random() > 0.6:
            refund_docs.append({
                "booking_id": f"dummy_bkg_{random.randint(1000,9999)}",
                "customer_id": customer_id,
                "amount": service["price"] * 0.8, # 20% cancellation fee
                "status": random.choice(["processed", "pending"]),
                "razorpay_refund_id": f"rfnd_{fake.pystr(min_chars=14, max_chars=14)}",
                "created_at": event_date + timedelta(days=1)
            })

        # Generate Chat History
        if random.random() > 0.5:
            chat_docs.append({
                "customer_id": customer_id,
                "vendor_id": service["vendor_id"],
                "messages": [
                    {"sender": "customer", "text": "Hi, is this date available?", "timestamp": created_date},
                    {"sender": "vendor", "text": "Yes, it is! Let me know your requirements.", "timestamp": created_date + timedelta(minutes=15)}
                ],
                "created_at": created_date
            })

        # Generate Support Tickets
        if random.random() > 0.9:
            ticket_docs.append({
                "user_id": customer_id,
                "subject": random.choice(["Payment failed but money deducted", "Change event date", "Vendor not responding"]),
                "status": random.choice(["open", "in_progress", "resolved"]),
                "priority": random.choice(["low", "medium", "high"]),
                "created_at": created_date + timedelta(days=1)
            })

    await db.bookings.insert_many(booking_docs)
    await db.reviews.insert_many(review_docs)
    await db.chats.insert_many(chat_docs)
    if refund_docs:
        await db.refunds.insert_many(refund_docs)
    if ticket_docs:
        await db.support_tickets.insert_many(ticket_docs)

    # Insert Time-Series Analytics Data
    analytics_docs = [{"date": k, "revenue": v["revenue"], "total_bookings": v["bookings"]} for k, v in analytics_data.items()]
    await db.analytics.insert_many(analytics_docs)

    print(f"✅ Generated {len(booking_docs)} Bookings & Transactions.")
    print(f"✅ Generated {len(review_docs)} Service Reviews.")
    print(f"✅ Generated {len(refund_docs)} Refunds & {len(ticket_docs)} Support Tickets.")
    print(f"✅ Populated Time-Series Analytics for Dashboards.")
    
    print("🎉 Production Data Engine Complete! Dashboards are fully hydrated.")
    client.close()

if __name__ == "__main__":
    asyncio.run(generate_dummy_data())