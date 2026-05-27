"""Update existing category names to match Phase 3 list."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
db_name = os.environ.get("DB_NAME", "shadiro_production")

# Exact names from requirements
UPDATES = {
    "cat-makeup": "Makeup Artists & Stylists",
    "cat-entertainment": "DJs, Bands, & Entertainers",
    "cat-transport": "Transport & Rental Services",
    "cat-mehandi": "Mehandi Designer",
}


async def migrate():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    for cat_id, new_name in UPDATES.items():
        result = await db.vendor_categories.update_one(
            {"id": cat_id},
            {"$set": {"name": new_name}}
        )
        if result.modified_count:
            print(f"Updated {cat_id} -> {new_name}")

    print("Category names updated.")
    client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
