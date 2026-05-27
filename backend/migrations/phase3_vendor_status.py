"""Phase 3 migration: Add vendor status and new fields to existing vendors."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
db_name = os.environ.get("DB_NAME", "shadiro_production")


async def migrate():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    # Add status=approved to vendors that don't have status (legacy)
    result = await db.vendors.update_many(
        {"status": {"$exists": False}},
        {"$set": {"status": "approved", "subscription_plan": "free", "is_featured": False}}
    )
    print(f"Updated {result.modified_count} vendors with status=approved")

    # Ensure all vendors have required new fields
    vendors = await db.vendors.find({}, {"id": 1}).to_list(1000)
    for v in vendors:
        updates = {}
        if "service_areas" not in v:
            updates["service_areas"] = []
        if "highlights" not in v:
            updates["highlights"] = []
        if "portfolio_urls" not in v:
            updates["portfolio_urls"] = []
        if updates:
            await db.vendors.update_one({"id": v["id"]}, {"$set": updates})

    print("Migration complete.")
    client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
