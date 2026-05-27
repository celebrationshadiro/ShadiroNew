"""Category-wise booking flow templates for progressive booking UX."""
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from api.deps import get_db
from services.category_booking_flow import get_booking_flow_template

router = APIRouter(prefix="/api/booking-flows", tags=["booking-flows"])


@router.get("/category/{category_id}")
async def get_category_booking_flow(category_id: str):
    template = get_booking_flow_template(category_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"No booking flow template for category: {category_id}")
    return template


@router.get("/vendor/{vendor_id}")
async def get_vendor_booking_flow(vendor_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    from core.cache import get_cache_service
    cache = get_cache_service()
    cache_key = f"booking_flow:{vendor_id}"
    
    cached = await cache.get(cache_key)
    if cached:
        return cached

    vendor = await db.vendors.find_one({"id": vendor_id}, {"_id": 0, "id": 1, "category_id": 1, "business_name": 1})
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    template = get_booking_flow_template(vendor.get("category_id"))
    if not template:
        res = {
            "category_id": vendor.get("category_id"),
            "vendor_id": vendor_id,
            "vendor_name": vendor.get("business_name"),
            "flow_version": "generic",
            "booking_inputs": [],
            "pricing_model": "custom",
            "advance_percentage": 30,
        }
        await cache.set(cache_key, res, 3600)
        return res

    template["vendor_id"] = vendor_id
    template["vendor_name"] = vendor.get("business_name")
    await cache.set(cache_key, template, 3600)
    return template
