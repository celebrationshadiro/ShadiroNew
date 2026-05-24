"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  SAFE TEST DATA CLEANUP SCRIPT                              ║
║              Removes only data with _seed_tag = "SEED_TEST_v1"              ║
║                                                                              ║
║  IMPORTANT: This script only deletes test data. Production data is SAFE ✅  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

SEED_TAG = "SEED_TEST_v1"
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "eventapp"

COLLECTIONS = [
    "users",
    "vendor_categories",
    "vendors",
    "booking_intents",
    "bookings",
    "payments",
    "vendor_ledger",
    "payouts",
    "refunds",
    "webhook_events",
    "resource_locks",
    "state_transitions",
    "notifications",
    "audit_logs",
    "grocery_items",
    "grocery_orders",
]

async def cleanup():
    """Clean up test data"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("\n" + "═"*70)
    print("🧹 TEST DATA CLEANUP")
    print("═"*70)
    
    # Count before deletion
    print("\n📊 DOCUMENTS TO BE DELETED (Before):")
    print("-" * 70)
    
    total_before = 0
    counts_before = {}
    
    for collection_name in COLLECTIONS:
        collection = db[collection_name]
        count = await collection.count_documents({"_seed_tag": SEED_TAG})
        counts_before[collection_name] = count
        total_before += count
        if count > 0:
            print(f"   {collection_name:<25}: {count:>5}")
    
    print("-" * 70)
    print(f"   {'TOTAL':<25}: {total_before:>5}")
    
    if total_before == 0:
        print("\n⚠️  No test data found to delete.")
        print("   Run seed_mongodb.py first to create test data.")
        client.close()
        return
    
    # Confirmation
    print("\n" + "⚠️  " * 10)
    print("\n🚨 DANGER ZONE 🚨")
    print(f"\nYou are about to DELETE {total_before} test documents.")
    print("\nThis action:")
    print("  ✅ WILL delete ONLY test data (_seed_tag = 'SEED_TEST_v1')")
    print("  ✅ WILL NOT affect production data")
    print("  ❌ CANNOT be undone programmatically (but DB backups exist)")
    
    print("\n" + "═"*70)
    confirmation = input("\nType 'DELETE' to confirm and permanently delete test data: ").strip()
    
    if confirmation != "DELETE":
        print("\n❌ Deletion cancelled.")
        print("   Test data remains intact.")
        client.close()
        return
    
    # Delete data
    print("\n🔄 Deleting test data from all collections...")
    print("-" * 70)
    
    counts_deleted = {}
    total_deleted = 0
    
    for collection_name in COLLECTIONS:
        collection = db[collection_name]
        result = await collection.delete_many({"_seed_tag": SEED_TAG})
        counts_deleted[collection_name] = result.deleted_count
        total_deleted += result.deleted_count
        
        if result.deleted_count > 0:
            print(f"   {collection_name:<25}: {result.deleted_count:>5} ✓")
    
    print("-" * 70)
    print(f"   {'TOTAL DELETED':<25}: {total_deleted:>5}")
    
    # Verify deletion
    print("\n🔍 Verification (After):")
    print("-" * 70)
    
    total_after = 0
    for collection_name in COLLECTIONS:
        collection = db[collection_name]
        count = await collection.count_documents({"_seed_tag": SEED_TAG})
        total_after += count
        if count > 0:
            print(f"   ⚠️  {collection_name:<23}: {count:>5} (PROBLEM!)")
    
    print("-" * 70)
    print(f"   {'TOTAL REMAINING':<25}: {total_after:>5}")
    
    # Final status
    print("\n" + "═"*70)
    if total_after == 0:
        print("✅ CLEANUP SUCCESSFUL!")
        print("═"*70)
        print("\n📊 Summary:")
        print(f"   Deleted: {total_deleted} test documents")
        print(f"   Remaining: {total_after} test documents")
        print("\n🔒 Real app data: SAFE ✅")
        print("\n💡 You can now:")
        print("   1. Run seed_mongodb.py again to reseed test data")
        print("   2. Verify your production data is intact")
        print("   3. Deploy to production with confidence")
        print("\n" + "═"*70 + "\n")
    else:
        print("❌ CLEANUP INCOMPLETE!")
        print("═"*70)
        print(f"\n⚠️  {total_after} test documents remain")
        print("\nThis might indicate:")
        print("   - Database connection issues")
        print("   - Permission issues")
        print("   - Database transaction errors")
        print("\n🔧 Troubleshooting:")
        print("   1. Check MongoDB is running: mongodb://localhost:27017")
        print("   2. Verify database exists:", DB_NAME)
        print("   3. Check connection permissions")
        print("   4. Review error logs above")
        print("\n" + "═"*70 + "\n")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(cleanup())
