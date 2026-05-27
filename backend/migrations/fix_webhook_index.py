"""
Migration script to fix webhook events index conflict.
Drops the old idx_webhook_events_received_at index to allow the new TTL index to be created.
"""

import asyncio
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "event_app_dev")


def fix_webhook_index():
    """Drop both conflicting indexes and create the correct TTL index."""
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    collection = db["webhook_events"]
    
    try:
        # Get all current indexes
        indexes = collection.list_indexes()
        index_names = [idx['name'] for idx in indexes]
        
        # Drop both potentially conflicting indexes if they exist
        if "idx_webhook_events_received_at" in index_names:
            print("Dropping old index 'idx_webhook_events_received_at'...")
            collection.drop_index("idx_webhook_events_received_at")
            print("✓ Index dropped")
            
        if "ttl_webhook_30d" in index_names:
            print("Dropping old index 'ttl_webhook_30d'...")
            collection.drop_index("ttl_webhook_30d")
            print("✓ Index dropped")
        
        # Create the correct TTL index
        print("Creating new TTL index 'ttl_webhook_30d'...")
        collection.create_index(
            [("received_at", 1)],
            expireAfterSeconds=2592000,
            name="ttl_webhook_30d"
        )
        print("✓ TTL index created successfully (30-day expiration)")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        client.close()
    
    return True


if __name__ == "__main__":
    print(f"Connecting to MongoDB at: {MONGO_URL}")
    print(f"Database: {DB_NAME}\n")
    
    success = fix_webhook_index()
    
    if success:
        print("\n✓ Migration completed successfully!")
    else:
        print("\n✗ Migration failed!")
        exit(1)
