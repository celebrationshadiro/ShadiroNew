import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

async def fix_admin():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['eventapp']
    
    # Check current admin user
    admin = await db.users.find_one({'email': 'admin@eventapp.com'})
    if admin:
        current_hash = admin.get('password_hash') or admin.get('hashed_password')
        print(f'Current hash (first 50 chars): {str(current_hash)[:50]}')
        has_bcrypt = '$2' in str(current_hash)
        print(f'Hash is bcrypt format: {has_bcrypt}')
    else:
        print('Admin user not found!')
        return
    
    # Create proper bcrypt hash
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    new_hash = pwd_context.hash('Test@1234')
    print(f'New bcrypt hash (first 50 chars): {new_hash[:50]}')
    
    # Update admin user with new hash
    result = await db.users.update_one(
        {'email': 'admin@eventapp.com'},
        {'$set': {'password_hash': new_hash, 'hashed_password': new_hash}}
    )
    print(f'Update result: {result.modified_count} document(s) modified')
    
    # Verify the update
    updated_admin = await db.users.find_one({'email': 'admin@eventapp.com'})
    updated_hash = updated_admin.get('password_hash') or updated_admin.get('hashed_password')
    print(f'Verified new hash (first 50 chars): {str(updated_hash)[:50]}')
    
    # Test verification
    is_valid = pwd_context.verify('Test@1234', updated_hash)
    print(f'✅ Password verification works: {is_valid}')

asyncio.run(fix_admin())
