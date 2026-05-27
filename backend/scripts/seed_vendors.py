"""Seed 100 realistic Indian vendors with categories."""
import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import Set

from dotenv import load_dotenv
from faker import Faker
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

fake = Faker("en_IN")

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "event_app_dev")

VENDOR_CATEGORIES = ["photographer", "caterer", "venue", "makeup", "planner"]


async def seed_vendors() -> None:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    print("Starting vendor seeding...")

    existing_emails: Set[str] = set()
    async for vendor in db.vendors.find({"email": {"$exists": True}}, {"email": 1}):
        existing_emails.add(vendor["email"])

    vendor_docs = []
    for idx in range(100):
        while True:
            email = fake.company_email()
            if email not in existing_emails:
                existing_emails.add(email)
                break

        vendor_docs.append(
            {
                "id": str(uuid.uuid4()),
                "name": fake.name(),
                "email": email,
                "phone": fake.phone_number(),
                "business_name": f"{fake.company()} - {VENDOR_CATEGORIES[idx % 5].title()}",
                "category": VENDOR_CATEGORIES[idx % 5],
                "category_id": f"cat_{VENDOR_CATEGORIES[idx % 5]}",
                "city": fake.city(),
                "state": fake.state(),
                "address": fake.address(),
                "is_active": True,
                "is_verified": False,
                "is_featured": False,
                "rating": round(3.5 + (idx % 15) * 0.1, 1),
                "reviews_count": idx % 50,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    result = await db.vendors.insert_many(vendor_docs)
    print(f"[OK] Inserted {len(result.inserted_ids)} vendors")
    print(f"  Categories: {', '.join(VENDOR_CATEGORIES)}")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed_vendors())
