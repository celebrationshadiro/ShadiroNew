"""
Run this once after deployment to create all DB indexes.
Usage: python run_migrations.py
       python run_migrations.py --dry-run
"""
import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient

DRY_RUN = "--dry-run" in sys.argv

async def run():
    uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/eventapp")
    client = AsyncIOMotorClient(uri)
    db = client.get_default_database()
    
    indexes = [
        # (collection, index_spec, kwargs)
        ("bookings", [("user_id", 1), ("created_at", -1)], {"name": "idx_bookings_user_date"}),
        ("bookings", [("vendor_id", 1), ("status", 1)], {"name": "idx_bookings_vendor_status"}),
        ("bookings", [("status", 1), ("created_at", -1)], {"name": "idx_bookings_status_date"}),
        ("vendor_ledger", [("vendor_id", 1), ("created_at", -1)], {"name": "idx_ledger_vendor_date"}),
        ("payouts", [("vendor_id", 1), ("status", 1)], {"name": "idx_payouts_vendor_status"}),
        ("payments", [("status", 1), ("created_at", -1)], {"name": "idx_payments_status_date"}),
        ("payments", [("booking_intent_id", 1)], {"name": "uniq_payments_intent", "unique": True}),
        ("webhook_events", [("event_id", 1)], {"name": "uniq_webhook_event_id", "unique": True}),
        ("booking_intents", [("expires_at", 1)], {"name": "ttl_booking_intents", "expireAfterSeconds": 0}),
        ("webhook_events", [("received_at", 1)], {"name": "ttl_webhook_30d", "expireAfterSeconds": 2592000}),
        ("grocery_products", [("vendor_id", 1), ("in_stock", 1)], {"name": "idx_grocery_products_stock"}),
        ("grocery_products", [("vendor_id", 1), ("category", 1)], {"name": "idx_grocery_products_cat"}),
        ("grocery_vendor_profiles", [("vendor_id", 1)], {"name": "uniq_grocery_profile", "unique": True}),
        ("grocery_vendor_profiles", [("city", 1), ("area", 1)], {"name": "idx_grocery_profile_location"}),
        ("grocery_vendor_profiles", [("pincode", 1)], {"name": "idx_grocery_profile_pincode"}),
        ("grocery_orders", [("idempotency_key", 1)], {"name": "uniq_grocery_order_idem", "unique": True}),
        ("grocery_orders", [("customer_id", 1), ("created_at", -1)], {"name": "idx_grocery_orders_customer"}),
        ("grocery_orders", [("vendor_id", 1), ("status", 1)], {"name": "idx_grocery_orders_vendor_status"}),
    ]
    
    print(f"\n{'[DRY RUN] ' if DRY_RUN else ''}Running {len(indexes)} index migrations...\n")
    
    for collection_name, index_spec, kwargs in indexes:
        label = f"{collection_name}: {kwargs['name']}"
        if DRY_RUN:
            print(f"  ⏭️  Would create: {label}")
            continue
        try:
            collection = db[collection_name]
            await collection.create_index(index_spec, **kwargs)
            print(f"  ✅ Created: {label}")
        except Exception as e:
            if "already exists" in str(e).lower() or "IndexKeySpecsConflict" in str(e):
                print(f"  ⏭️  Skipped (exists): {label}")
            else:
                print(f"  ❌ Failed: {label} — {e}")
    
    print("\nMigration complete.\n")
    client.close()

asyncio.run(run())
