"""Add Grocery Vendors category."""
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

    existing = await db.vendor_categories.find_one({"id": "cat-grocery"})
    if existing:
        print("Grocery category already exists.")
    else:
        await db.vendor_categories.insert_one({
            "id": "cat-grocery",
            "name": "Grocery Vendors",
            "slug": "grocery",
            "description": "Fresh groceries and supplies for your events",
            "icon": "ShoppingBag",
            "image_url": "https://images.unsplash.com/photo-1542838132-92c53300491e"
        })
        print("Added Grocery Vendors category.")

    client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
