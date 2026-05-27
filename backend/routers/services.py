"""Vendor service items management - category-specific items like menu items, equipment, etc."""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

from models import ServiceItem, ServiceDefinition, UserRole, VendorType
from auth import require_role
from services.vendor_type import resolve_vendor_type
from api.deps import get_db

router = APIRouter(prefix="/api/services", tags=["services"])
logger = logging.getLogger(__name__)


# --- VENDOR SERVICE ITEM MANAGEMENT ---

@router.get("/vendor/{vendor_id}/items")
async def get_vendor_service_items(
    vendor_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get all service items for a vendor (public endpoint for booking UI)."""

    vendor = await db.vendors.find_one({"id": vendor_id}, {"_id": 0, "category_id": 1, "vendor_type": 1})
    if vendor and resolve_vendor_type(vendor.get("category_id"), vendor.get("vendor_type")) == VendorType.PRODUCT_VENDOR:
        return {"items": [], "category_id": vendor.get("category_id")}

    definition = await db.service_definitions.find_one(
        {"vendor_id": vendor_id},
        {"_id": 0}
    )
    
    if not definition:
        # Return empty list if no services defined yet
        return {"items": []}
    
    items = definition.get("service_items", [])
    return {"items": items, "category_id": definition.get("category_id")}


@router.post("/vendor/items/add")
async def add_service_item(
    item: ServiceItem,
    current_user: dict = Depends(require_role([UserRole.VENDOR])),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Vendor adds a new service item to their offerings."""
    
    user_id = current_user.get("sub")
    vendor = await db.vendors.find_one({"user_id": user_id}, {"_id": 0, "id": 1, "category_id": 1, "vendor_type": 1})
    
    if not vendor:
        raise HTTPException(status_code=403, detail="Vendor profile not found")
    
    if resolve_vendor_type(vendor.get("category_id"), vendor.get("vendor_type")) == VendorType.PRODUCT_VENDOR:
        raise HTTPException(status_code=400, detail="Grocery vendors do not use service items")

    vendor_id = vendor.get("id")
    category_id = vendor.get("category_id")
    
    # Validation
    if item.vendor_id != vendor_id:
        raise HTTPException(status_code=403, detail="Cannot add items for another vendor")
    
    if item.category_id != category_id:
        raise HTTPException(status_code=400, detail="Item category must match vendor category")
    
    # Ensure service definition exists
    definition = await db.service_definitions.find_one({"vendor_id": vendor_id}, {"_id": 0})
    
    if not definition:
        # Create new service definition
        definition = ServiceDefinition(
            vendor_id=vendor_id,
            category_id=category_id,
            service_items=[item]
        )
        definition_doc = definition.model_dump()
        definition_doc["created_at"] = definition_doc["created_at"].isoformat()
        await db.service_definitions.insert_one(definition_doc)
    else:
        # Append item to existing definition
        item_doc = item.model_dump()
        item_doc["created_at"] = item_doc["created_at"].isoformat()
        await db.service_definitions.update_one(
            {"vendor_id": vendor_id},
            {
                "$push": {"service_items": item_doc},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
    
    return {"status": "success", "item_id": item.id}


@router.put("/vendor/items/{item_id}")
async def update_service_item(
    item_id: str,
    update_data: dict,
    current_user: dict = Depends(require_role([UserRole.VENDOR])),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Vendor updates a service item."""
    
    user_id = current_user.get("sub")
    vendor = await db.vendors.find_one({"user_id": user_id}, {"_id": 0, "id": 1, "category_id": 1, "vendor_type": 1})
    
    if not vendor:
        raise HTTPException(status_code=403, detail="Vendor profile not found")
    
    if resolve_vendor_type(vendor.get("category_id"), vendor.get("vendor_type")) == VendorType.PRODUCT_VENDOR:
        raise HTTPException(status_code=400, detail="Grocery vendors do not use service items")

    vendor_id = vendor.get("id")
    
    # Find and update the item in the service definition
    result = await db.service_definitions.find_one_and_update(
        {"vendor_id": vendor_id, "service_items.id": item_id},
        {
            "$set": {
                "service_items.$.name": update_data.get("name"),
                "service_items.$.unit_price": update_data.get("unit_price"),
                "service_items.$.unit": update_data.get("unit"),
                "service_items.$.description": update_data.get("description"),
                "service_items.$.is_available": update_data.get("is_available", True),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        },
        return_document=True,
        projection={"_id": 0}
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Service item not found")
    
    return {"status": "success", "message": "Item updated"}


@router.delete("/vendor/items/{item_id}")
async def delete_service_item(
    item_id: str,
    current_user: dict = Depends(require_role([UserRole.VENDOR])),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Vendor deletes a service item."""
    
    user_id = current_user.get("sub")
    vendor = await db.vendors.find_one({"user_id": user_id}, {"_id": 0, "id": 1, "category_id": 1, "vendor_type": 1})
    
    if not vendor:
        raise HTTPException(status_code=403, detail="Vendor profile not found")
    
    if resolve_vendor_type(vendor.get("category_id"), vendor.get("vendor_type")) == VendorType.PRODUCT_VENDOR:
        raise HTTPException(status_code=400, detail="Grocery vendors do not use service items")

    vendor_id = vendor.get("id")
    
    # Remove the item from service definition
    result = await db.service_definitions.find_one_and_update(
        {"vendor_id": vendor_id},
        {"$pull": {"service_items": {"id": item_id}}},
        return_document=True,
        projection={"_id": 0}
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Service item not found")
    
    return {"status": "success", "message": "Item deleted"}


# --- CATEGORY TEMPLATES (Pre-defined service structures per category)

CATEGORY_SERVICE_TEMPLATES = {
    "caterer": {
        "service_categories": ["appetizers", "main_course", "desserts", "beverages"],
        "unit": "per_plate",
        "example_items": [
            {"name": "Paneer Tikka", "service_category": "appetizers", "unit": "per_plate", "unit_price": 250},
            {"name": "Biryani", "service_category": "main_course", "unit": "per_plate", "unit_price": 350},
            {"name": "Gulab Jamun", "service_category": "desserts", "unit": "per_plate", "unit_price": 100},
        ]
    },
    "dj": {
        "service_categories": ["equipment", "services", "packages"],
        "unit": "item",
        "example_items": [
            {"name": "Sound System", "service_category": "equipment", "unit": "item", "unit_price": 1500},
            {"name": "Lights & Effects", "service_category": "equipment", "unit": "item", "unit_price": 800},
            {"name": "DJ Trolley", "service_category": "equipment", "unit": "item", "unit_price": 300},
            {"name": "Backup Power", "service_category": "equipment", "unit": "item", "unit_price": 500},
            {"name": "4 Hour Performance", "service_category": "services", "unit": "per_hour", "unit_price": 1000},
        ]
    },
    "photographer": {
        "service_categories": ["packages", "add_ons", "deliverables"],
        "unit": "package",
        "example_items": [
            {"name": "Album (200 photos)", "service_category": "deliverables", "unit": "package", "unit_price": 5000},
            {"name": "Video (2 hours)", "service_category": "deliverables", "unit": "package", "unit_price": 8000},
            {"name": "Pre-wedding shoot", "service_category": "packages", "unit": "package", "unit_price": 3000},
        ]
    },
    "makeup_artist": {
        "service_categories": ["services", "add_ons"],
        "unit": "item",
        "example_items": [
            {"name": "Bridal Makeup", "service_category": "services", "unit": "item", "unit_price": 3000},
            {"name": "Regular Makeup", "service_category": "services", "unit": "item", "unit_price": 1500},
            {"name": "Hair Styling", "service_category": "services", "unit": "item", "unit_price": 1000},
        ]
    },
    "decorator": {
        "service_categories": ["themes", "items", "setup"],
        "unit": "item",
        "example_items": [
            {"name": "Floral Arch", "service_category": "items", "unit": "item", "unit_price": 5000},
            {"name": "Table Arrangements", "service_category": "items", "unit": "item", "unit_price": 2000},
            {"name": "Entrance Decoration", "service_category": "setup", "unit": "item", "unit_price": 3000},
        ]
    },
    "grocery": {
        "service_categories": ["grains", "oils", "vegetables", "menu_items"],
        "unit": "kg",
        "example_items": [
            {"name": "Rice", "service_category": "grains", "unit": "kg", "unit_price": 80},
            {"name": "Wheat", "service_category": "grains", "unit": "kg", "unit_price": 60},
            {"name": "Cooking Oil", "service_category": "oils", "unit": "litre", "unit_price": 140},
            {"name": "Seasonal Vegetables", "service_category": "vegetables", "unit": "kg", "unit_price": 70},
        ]
    },
    "planner": {
        "service_categories": ["planning", "coordination", "vendors"],
        "unit": "package",
        "example_items": [
            {"name": "Full Event Planning", "service_category": "planning", "unit": "package", "unit_price": 25000},
            {"name": "Vendor Coordination", "service_category": "vendors", "unit": "package", "unit_price": 15000},
            {"name": "On-site Management", "service_category": "coordination", "unit": "package", "unit_price": 12000},
        ]
    }
}


@router.get("/category-template/{category_id}")
async def get_category_template(category_id: str):
    """Get pre-defined service template for a category."""
    template = CATEGORY_SERVICE_TEMPLATES.get(category_id, {})
    
    if not template:
        raise HTTPException(status_code=404, detail=f"No template for category: {category_id}")
    
    return {
        "category_id": category_id,
        "template": template,
        "message": "Use this template to define your service items"
    }


@router.post("/vendor/bulk-add-items")
async def bulk_add_service_items(
    items: List[ServiceItem],
    current_user: dict = Depends(require_role([UserRole.VENDOR])),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Vendor adds multiple service items at once (e.g., from template)."""
    
    user_id = current_user.get("sub")
    vendor = await db.vendors.find_one({"user_id": user_id}, {"_id": 0, "id": 1, "category_id": 1, "vendor_type": 1})
    
    if not vendor:
        raise HTTPException(status_code=403, detail="Vendor profile not found")
    
    if resolve_vendor_type(vendor.get("category_id"), vendor.get("vendor_type")) == VendorType.PRODUCT_VENDOR:
        raise HTTPException(status_code=400, detail="Grocery vendors do not use service items")

    vendor_id = vendor.get("id")
    category_id = vendor.get("category_id")
    
    # Validate all items
    for item in items:
        if item.vendor_id != vendor_id or item.category_id != category_id:
            raise HTTPException(status_code=400, detail="Item vendor/category mismatch")
    
    # Get or create service definition
    definition = await db.service_definitions.find_one({"vendor_id": vendor_id}, {"_id": 0})
    
    items_docs = [item.model_dump() for item in items]
    for doc in items_docs:
        doc["created_at"] = doc["created_at"].isoformat()
    
    if not definition:
        # Create new definition with all items
        definition = ServiceDefinition(
            vendor_id=vendor_id,
            category_id=category_id,
            service_items=items
        )
        definition_doc = definition.model_dump()
        definition_doc["created_at"] = definition_doc["created_at"].isoformat()
        definition_doc["service_items"] = items_docs
        await db.service_definitions.insert_one(definition_doc)
    else:
        # Append items to existing definition
        await db.service_definitions.update_one(
            {"vendor_id": vendor_id},
            {
                "$push": {"service_items": {"$each": items_docs}},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
    
    return {
        "status": "success",
        "items_added": len(items),
        "total_items": len(definition.get("service_items", []) if definition else items)
    }
