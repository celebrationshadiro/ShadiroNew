"""
Fix password hashing issues - handles invalid/missing hashes and field name inconsistencies.

Issues addressed:
1. Users with invalid bcrypt hashes (UnknownHashError)
2. Inconsistent field names (password_hash vs hashed_password)
3. Plain text passwords stored in database
4. Missing password hashes

Strategy:
- Consolidate to 'password_hash' field for consistency
- Identify and flag users with invalid hashes
- Generate temporary random passwords for broken accounts (users must reset)
- Log all changes for audit purposes
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path
import uuid

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
db_name = os.environ.get("DB_NAME", "shadiro_production")


def get_password_hash(password: str) -> str:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)


def is_valid_bcrypt_hash(hashed_password: str) -> bool:
    """Check if a hash is a valid bcrypt hash."""
    if not hashed_password or not isinstance(hashed_password, str):
        return False
    # Bcrypt hashes start with $2a$, $2b$, $2x$, or $2y$
    return hashed_password.startswith(('$2a$', '$2b$', '$2x$', '$2y$'))


async def fix_password_hashes():
    """Fix password hashing issues in the database."""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    fixed_count = 0
    flagged_count = 0
    consolidated_count = 0
    stats = {
        "total_users": 0,
        "valid_hashes": 0,
        "invalid_hashes": 0,
        "missing_hashes": 0,
        "field_consolidated": 0,
        "plain_text_detected": 0,
    }

    print("Starting password hash migration...")
    print(f"Database: {db_name}\n")

    # Get all users
    users = await db.users.find({}, {"_id": 0}).to_list(None)
    stats["total_users"] = len(users)

    print(f"Found {len(users)} users to check\n")

    for user in users:
        user_id = user.get("id") or user.get("_id")
        email = user.get("email", "unknown")

        # Check for password field inconsistencies
        password_hash = user.get("password_hash")
        hashed_password = user.get("hashed_password")

        update_doc = {}
        needs_update = False

        # Consolidate field names - prefer password_hash
        if hashed_password and not password_hash:
            # Migrate hashed_password to password_hash
            if is_valid_bcrypt_hash(hashed_password):
                update_doc["password_hash"] = hashed_password
                update_doc["$unset"] = {"hashed_password": ""}
                stats["field_consolidated"] += 1
                consolidated_count += 1
                needs_update = True
            else:
                # Invalid hash in hashed_password field
                stats["invalid_hashes"] += 1
                password_hash = hashed_password  # Use it anyway for validation

        # Check password_hash validity
        if not password_hash:
            stats["missing_hashes"] += 1
            # Generate a temporary hash (user will need to reset password)
            temp_password = f"TEMP_{uuid.uuid4().hex[:12]}"
            update_doc["password_hash"] = get_password_hash(temp_password)
            update_doc["password_reset_required"] = True
            flagged_count += 1
            needs_update = True
            print(f"⚠️  {email} ({user_id}): Missing password - generated temporary password")

        elif not is_valid_bcrypt_hash(password_hash):
            stats["invalid_hashes"] += 1

            # Check if it might be plain text (no special chars or short)
            if len(password_hash) < 30 or not any(c in password_hash for c in ['$', '.', '/']):
                stats["plain_text_detected"] += 1
                print(f"⚠️  {email} ({user_id}): Plain text password detected")
            else:
                print(f"⚠️  {email} ({user_id}): Invalid hash format")

            # Generate temporary password for flagged account
            temp_password = f"TEMP_{uuid.uuid4().hex[:12]}"
            update_doc["password_hash"] = get_password_hash(temp_password)
            update_doc["password_reset_required"] = True
            flagged_count += 1
            needs_update = True
        else:
            stats["valid_hashes"] += 1

        # Perform the update
        if needs_update:
            try:
                update_doc["updated_at"] = datetime.now(timezone.utc)
                result = await db.users.update_one(
                    {"id": user_id} if user.get("id") else {"_id": user_id},
                    {"$set": update_doc} if "$unset" not in update_doc
                    else {"$set": {k: v for k, v in update_doc.items() if k != "$unset"},
                          "$unset": update_doc["$unset"]}
                )
                if result.modified_count > 0:
                    fixed_count += 1
            except Exception as e:
                print(f"❌ Error updating {email} ({user_id}): {e}")

    # Log migration summary
    print("\n" + "="*60)
    print("MIGRATION SUMMARY")
    print("="*60)
    print(f"Total users processed: {stats['total_users']}")
    print(f"Valid bcrypt hashes: {stats['valid_hashes']}")
    print(f"Invalid hashes found: {stats['invalid_hashes']}")
    print(f"Missing hashes: {stats['missing_hashes']}")
    print(f"Plain text passwords detected: {stats['plain_text_detected']}")
    print(f"Field names consolidated: {stats['field_consolidated']}")
    print(f"\nTotal fixes applied: {fixed_count}")
    print(f"Total accounts flagged (requiring password reset): {flagged_count}")

    if flagged_count > 0:
        print(f"\n⚠️  {flagged_count} accounts have been flagged with 'password_reset_required'")
        print("   These users should be notified to reset their passwords")

    print("\n" + "="*60)

    client.close()


if __name__ == "__main__":
    asyncio.run(fix_password_hashes())
