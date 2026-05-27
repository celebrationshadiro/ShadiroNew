"""
Test to verify ObjectId serialization fix in recommendation engine.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from bson import ObjectId
from services.recommendation_engine import convert_objectids_to_strings


def test_convert_objectids_simple():
    """Test converting a simple ObjectId."""
    oid = ObjectId()
    result = convert_objectids_to_strings(oid)
    assert isinstance(result, str), "ObjectId should be converted to string"
    assert len(result) == 24, "Converted ObjectId should be 24 chars"
    print("✓ Simple ObjectId conversion works")


def test_convert_objectids_in_dict():
    """Test converting ObjectIds nested in a dict."""
    doc = {
        "_id": ObjectId(),
        "user_id": ObjectId(),
        "name": "Test Vendor",
        "rating": 4.5,
    }
    result = convert_objectids_to_strings(doc)
    
    assert isinstance(result["_id"], str), "_id should be string"
    assert isinstance(result["user_id"], str), "user_id should be string"
    assert isinstance(result["name"], str), "name should remain string"
    assert isinstance(result["rating"], float), "rating should remain float"
    print("✓ Dict with ObjectIds conversion works")


def test_convert_objectids_nested():
    """Test converting ObjectIds in deeply nested structures."""
    doc = {
        "_id": ObjectId(),
        "vendor_info": {
            "category_id": ObjectId(),
            "tags": ["wedding", "corporate"],
        },
        "reviews": [
            {
                "review_id": ObjectId(),
                "user_id": ObjectId(),
                "text": "Great service",
            }
        ],
    }
    result = convert_objectids_to_strings(doc)
    
    assert isinstance(result["_id"], str), "Top-level _id should be string"
    assert isinstance(result["vendor_info"]["category_id"], str), "Nested category_id should be string"
    assert isinstance(result["reviews"][0]["review_id"], str), "Review _id should be string"
    assert isinstance(result["reviews"][0]["user_id"], str), "Review user_id should be string"
    assert result["vendor_info"]["tags"] == ["wedding", "corporate"], "Lists should be preserved"
    print("✓ Deeply nested ObjectIds conversion works")


def test_convert_objectids_list():
    """Test converting a list of documents with ObjectIds."""
    docs = [
        {
            "_id": ObjectId(),
            "vendor_id": ObjectId(),
            "name": "Vendor 1",
        },
        {
            "_id": ObjectId(),
            "vendor_id": ObjectId(),
            "name": "Vendor 2",
        },
    ]
    result = convert_objectids_to_strings(docs)
    
    assert isinstance(result, list), "Result should be a list"
    assert len(result) == 2, "List length should be preserved"
    for doc in result:
        assert isinstance(doc["_id"], str), "Each _id should be string"
        assert isinstance(doc["vendor_id"], str), "Each vendor_id should be string"
    print("✓ List of documents with ObjectIds conversion works")


def test_no_objectids():
    """Test that non-ObjectId data is preserved."""
    doc = {
        "name": "Vendor",
        "rating": 4.5,
        "tags": ["wedding", "corporate"],
        "metadata": {
            "created": "2026-05-15",
            "active": True,
        },
    }
    result = convert_objectids_to_strings(doc)
    
    assert result == doc, "Non-ObjectId data should be preserved exactly"
    print("✓ Non-ObjectId data preservation works")


if __name__ == "__main__":
    test_convert_objectids_simple()
    test_convert_objectids_in_dict()
    test_convert_objectids_nested()
    test_convert_objectids_list()
    test_no_objectids()
    print("\n✅ All ObjectId serialization tests passed!")
