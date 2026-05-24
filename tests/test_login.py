#!/usr/bin/env python
"""Test password verification with fixed bcrypt version"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

async def test_login():
    """Test that password verification works"""
    client = AsyncIOMotorClient(os.getenv('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.getenv('DB_NAME', 'shadiro_db')]
    
    # Get admin user from database
    admin = await db.users.find_one({'email': 'admin@eventapp.com'})
    if not admin:
        print("❌ Admin user not found in database!")
        return False
    
    stored_hash = admin.get('password_hash') or admin.get('hashed_password')
    print(f"✅ Found admin user: {admin.get('email')}")
    print(f"✅ Hash format: {stored_hash[:30]}...")
    
    # Create context (same as in security.py)
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Test verification
    try:
        is_valid = pwd_context.verify('Test@1234', stored_hash)
        print(f"✅ Password verification result: {is_valid}")
        
        if is_valid:
            print("\n" + "="*60)
            print("✅ SUCCESS: Password verification is working!")
            print("="*60)
            print("\nLogin credentials:")
            print(f"  Email: admin@eventapp.com")
            print(f"  Password: Test@1234")
            print("\nYou can now:")
            print("  1. Start the backend: python server.py")
            print("  2. Login via: http://localhost:3000/admin/login")
            print("="*60)
            return True
        else:
            print("❌ Password verification failed (invalid password)")
            return False
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

if __name__ == '__main__':
    result = asyncio.run(test_login())
    exit(0 if result else 1)
