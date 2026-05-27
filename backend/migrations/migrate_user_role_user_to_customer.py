"""Migrate legacy user role value 'user' to canonical 'customer'."""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "shadiro_production")


async def run() -> None:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    result = await db.users.update_many({"role": "user"}, {"$set": {"role": "customer"}})
    print(
        {
            "matched": result.matched_count,
            "modified": result.modified_count,
            "from_role": "user",
            "to_role": "customer",
        }
    )
    client.close()


if __name__ == "__main__":
    asyncio.run(run())
