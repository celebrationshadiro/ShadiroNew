"""
Pytest configuration and fixtures for Phase 3 E2E tests.
"""

import pytest
import asyncio
import os
from typing import Generator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from datetime import datetime, timedelta
from bson import ObjectId
import jwt


# Database fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def mongodb_connection():
    """Create MongoDB test database connection."""
    mongo_url = os.getenv(
        "MONGO_URL_TEST", "mongodb://localhost:27017/shadiro_test"
    )
    client = AsyncIOMotorClient(mongo_url)
    db = client["shadiro_test"]
    
    yield db
    
    # Cleanup
    await client.drop_database("shadiro_test")
    client.close()


@pytest.fixture
async def db(mongodb_connection):
    """Provide test database."""
    # Clear db before each test
    collections = await mongodb_connection.list_collection_names()
    for collection_name in collections:
        await mongodb_connection[collection_name].delete_many({})
    
    return mongodb_connection


# Authentication fixtures
@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "password": "test_password_123",
        "phone": "9999999999",
        "role": "user",
    }


@pytest.fixture
def test_vendor_data():
    """Test vendor data"""
    return {
        "business_name": "Premium Event Services",
        "category": "caterer",
        "city": "Mumbai",
        "state": "Maharashtra",
        "description": "Premium catering services",
        "min_price": 50000,
        "max_price": 200000,
        "phone": "8888888888",
        "email": "vendor@example.com",
        "average_rating": 4.5,
    }


@pytest.fixture
def jwt_token(test_user_data):
    """Generate JWT token for authentication."""
    SECRET_KEY = os.getenv("SECRET_KEY", "test_secret_key")
    payload = {
        "sub": str(ObjectId()),
        "email": test_user_data["email"],
        "role": "user",
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


@pytest.fixture
def auth_headers(jwt_token):
    """Provide authentication headers."""
    return {"Authorization": f"Bearer {jwt_token}"}


# API client fixtures
@pytest.fixture
def client():
    """Provide FastAPI test client."""
    from fastapi.testclient import TestClient
    from backend.server import app

    return TestClient(app)


# Sample data fixtures
@pytest.fixture
async def sample_user(db, test_user_data):
    """Create a sample user in database."""
    from backend.auth import get_password_hash

    user_doc = {
        "_id": ObjectId(),
        "email": test_user_data["email"],
        "name": test_user_data["name"],
        "phone": test_user_data["phone"],
        "role": test_user_data["role"],
        "hashed_password": get_password_hash(test_user_data["password"]),
        "created_at": datetime.utcnow(),
    }

    await db.users.insert_one(user_doc)
    return user_doc


@pytest.fixture
async def sample_vendor(db, test_vendor_data):
    """Create a sample vendor in database."""
    vendor_doc = {
        "_id": ObjectId(),
        "user_id": ObjectId(),
        "business_name": test_vendor_data["business_name"],
        "category": test_vendor_data["category"],
        "city": test_vendor_data["city"],
        "state": test_vendor_data["state"],
        "description": test_vendor_data["description"],
        "min_price": test_vendor_data["min_price"],
        "max_price": test_vendor_data["max_price"],
        "avg_rating": test_vendor_data["average_rating"],
        "review_count": 25,
        "status": "approved",
        "is_available": True,
        "years_of_experience": 5,
        "portfolio_count": 30,
        "created_at": datetime.utcnow(),
    }

    await db.vendors.insert_one(vendor_doc)
    return vendor_doc


@pytest.fixture
async def sample_booking(db, sample_user, sample_vendor):
    """Create a sample booking."""
    booking_doc = {
        "_id": ObjectId(),
        "user_id": sample_user["_id"],
        "vendor_id": sample_vendor["_id"],
        "event_date": datetime.utcnow() + timedelta(days=30),
        "status": "confirmed",
        "amount": 100000,
        "payment_status": "completed",
        "special_instructions": "Please ensure vegetarian options",
        "created_at": datetime.utcnow(),
    }

    await db.bookings.insert_one(booking_doc)
    return booking_doc


# Pytest marks
def pytest_configure(config):
    """Register custom pytest marks."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )


# Async test runner
@pytest.fixture
def run_async(event_loop):
    """Run async functions in tests."""
    def runner(coro):
        return event_loop.run_until_complete(coro)
    return runner


if __name__ == "__main__":
    pytest.main(["-v", "--tb=short"])
