"""Create admin user - run once to set up first admin."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
db_name = os.environ.get("DB_NAME", "shadiro_production")

# Set these or pass as env vars
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@shadiro.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin123!")
ADMIN_NAME = os.environ.get("ADMIN_NAME", "Shadiro Admin")


def get_password_hash(password: str) -> str:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)


async def create_admin():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    existing = await db.users.find_one({"email": ADMIN_EMAIL}, {"_id": 0})
    if existing:
        if existing.get("role") == "admin":
            print(f"Admin user {ADMIN_EMAIL} already exists.")
        else:
            await db.users.update_one(
                {"email": ADMIN_EMAIL},
                {"$set": {"role": "admin"}}
            )
            print(f"Updated {ADMIN_EMAIL} to admin role.")
        client.close()
        return

    user_id = str(uuid.uuid4())
    hashed = get_password_hash(ADMIN_PASSWORD)
    user_doc = {
        "id": user_id,
        "email": ADMIN_EMAIL,
        "name": ADMIN_NAME,
        "phone": None,
        "role": "admin",
        "password_hash": hashed,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True,
    }
    await db.users.insert_one(user_doc)
    print(f"Admin user created: {ADMIN_EMAIL}")
    print("Login with the credentials above.")
    client.close()


if __name__ == "__main__":
    asyncio.run(create_admin())
