# Password Hashing Fix - Implementation Guide

## Issues Fixed

### 1. **Invalid Password Hashes**
- **Error**: `passlib.exc.UnknownHashError: hash could not be identified`
- **Root Cause**: Database contains invalid hash formats or plain text passwords stored without hashing
- **Solution**: Migration script identifies and regenerates temporary hashes for broken accounts

### 2. **Inconsistent Field Names**
- **Problem**: Some users stored with `password_hash`, others with `hashed_password`
- **Solution**: Consolidated all to use `password_hash` field name (standard in codebase)

### 3. **Register/Admin Endpoints Using Different Fields**
- **Problem**: `create_admin_user.py` used `hashed_password`, but login/register use `password_hash`
- **Solution**: Updated all endpoints to use `password_hash`

## Files Changed

### 1. `backend/core/security.py`
✅ No changes needed - password hashing functions are correct:
- `hash_password(password)` - uses bcrypt via CryptContext
- `verify_password(plain_password, hashed_password)` - uses bcrypt verification

### 2. `backend/routers/auth.py`
✅ **Updated** - Login endpoint now:
- Handles both field names during transition (backward compatible)
- Checks for `password_reset_required` flag (set by migration)
- Directs flagged users to use forgot-password flow to reset

### 3. `backend/migrations/create_admin_user.py`
✅ **Fixed** - Changed field name from `hashed_password` to `password_hash`

### 4. `backend/migrations/fix_password_hashes.py` (NEW)
✅ **Created** - Comprehensive migration script that:
- Identifies users with invalid bcrypt hashes
- Detects plain text passwords
- Consolidates field names (`hashed_password` → `password_hash`)
- Generates temporary passwords for broken accounts
- Sets `password_reset_required` flag
- Provides detailed audit log

## Running the Migration

### Step 1: Backup Database
```bash
# Ensure you have a backup before running migrations
mongodump --uri="mongodb://..." --out=./backup
```

### Step 2: Run Password Hash Fix
```bash
cd backend
python migrations/fix_password_hashes.py
```

**Output**: You'll see:
- Total users processed
- Valid vs invalid hashes breakdown
- Count of accounts requiring password reset
- Detailed log of changes

### Step 3: Notify Users
Any users with `password_reset_required=true` need to:
1. Visit the "Forgot Password" page
2. Enter their email
3. Follow the reset link to set a new password

Users can still use forgot-password if they never had a valid password.

## What Happens After Migration

### For Users with Invalid Passwords:
1. Login attempt will be rejected with: "Password reset required - please use forgot password to set a new password"
2. They use the forgot-password flow to reset
3. Once reset, `password_reset_required` flag is removed automatically

### For Users with Valid Passwords:
- No impact - they login normally

## Security Best Practices Enforced

✅ **All passwords are hashed with bcrypt**
- 12 rounds default
- Scheme: `schemes=["bcrypt"]`

✅ **Password field is standardized**
- Field name: `password_hash` (consistent across all endpoints)
- Never store plain text passwords

✅ **Secure password reset flow**
- JWT token for reset (15 min expiration)
- One-time use enforcement
- User status checks (is_active, not is_blocked)

## Checking Status After Migration

```python
# Check how many users need password reset
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient("mongodb://...")
db = client["shadiro_production"]

flagged = await db.users.count_documents({"password_reset_required": True})
print(f"Users requiring password reset: {flagged}")

# Check users with valid passwords
valid = await db.users.count_documents({"password_hash": {"$regex": "^\\$2"}})
print(f"Users with valid bcrypt hashes: {valid}")
```

## Troubleshooting

### "UnknownHashError" still occurs after migration
- Ensure migration completed successfully
- Check database for any remaining plain text passwords
- Verify all users have `password_hash` field (not `hashed_password`)

### Users can't login after migration
- Check if they have `password_reset_required: true`
- Direct them to forgot-password flow
- Verify `password_hash` is a valid bcrypt hash: `$2a$..., $2b$..., $2x$..., $2y$...`

### Need to manually reset a user's password
```python
from core.security import hash_password

temp_password = "TempPassword123!"
hashed = hash_password(temp_password)

await db.users.update_one(
    {"email": "user@example.com"},
    {"$set": {
        "password_hash": hashed,
        "password_reset_required": True,
        "updated_at": datetime.now(timezone.utc)
    }}
)
```

## Verification Checklist

- [ ] Backup database before running migration
- [ ] Run migration script successfully
- [ ] Check migration output for flagged accounts
- [ ] Test login with valid credentials
- [ ] Test login with invalid password (should fail)
- [ ] Test with flagged account (should require reset)
- [ ] Verify forgot-password flow works
- [ ] Verify password reset removes the flag
- [ ] Check no users have plain text passwords
