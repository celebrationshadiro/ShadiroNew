from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, File, Query, Request, UploadFile

from app.api.v1.controllers.catalog_controller import catalog_controller
from app.api.v1.dependencies.pagination import Pagination, pagination_params
from app.api.v1.schemas.catalog import (
    CategoryUpsert,
    EventCreate,
    PackageCreate,
    PackagePatch,
    QuoteCreate,
    QuoteRespond,
    ReviewCreate,
    VendorCreate,
    VendorPatch,
)
from canonical_models.common import ResponseEnvelope
from core.database import get_db_from_request
from core.security import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api", tags=["catalog"])


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


@router.get("/categories", response_model=ResponseEnvelope[list[dict[str, Any]]])
async def list_categories(request: Request):
    data = await catalog_controller.list_categories(get_db_from_request(request))
    return ResponseEnvelope[list[dict[str, Any]]](
        success=True,
        data=data,
        message="Categories fetched",
        request_id=_request_id(request),
    )


@router.put("/categories/{slug}", response_model=ResponseEnvelope[dict[str, Any]])
async def upsert_category(
    slug: str,
    payload: CategoryUpsert,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    normalized = payload.model_copy(update={"slug": slug})
    data = await catalog_controller.upsert_category(get_db_from_request(request), normalized, current_user)
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Category saved",
        request_id=_request_id(request),
    )


@router.get("/vendors", response_model=ResponseEnvelope[dict[str, Any]])
async def list_vendors(
    request: Request,
    pagination: Pagination = Depends(pagination_params),
    category_id: Optional[str] = None,
    city: Optional[str] = None,
    q: Optional[str] = None,
    cursor: Optional[str] = Query(default=None),
    include_inactive: bool = False,
    current_user: Optional[dict[str, Any]] = Depends(get_current_user_optional),
):
    can_include_inactive = include_inactive and str((current_user or {}).get("role", "")).lower() == "admin"
    data = await catalog_controller.list_vendors(
        get_db_from_request(request),
        pagination,
        category_id=category_id,
        city=city,
        q=q,
        cursor=cursor,
        include_inactive=can_include_inactive,
    )
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Vendors fetched",
        request_id=_request_id(request),
    )


@router.get("/vendors/{city}/{category}", response_model=ResponseEnvelope[dict[str, Any]])
async def list_vendors_by_city_category(
    city: str,
    category: str,
    request: Request,
    pagination: Pagination = Depends(pagination_params),
):
    from core.cache import get_cache_service
    cache = get_cache_service()
    n = pagination.page
    cache_key = f"vendor_list:{city.lower()}:{category.lower()}:page:{n}"
    
    cached = await cache.get(cache_key)
    if cached:
        return ResponseEnvelope[dict[str, Any]](
            success=True,
            data=cached,
            message="Vendors fetched (cached)",
            request_id=_request_id(request),
        )

    # Normalize category name/alias using standard helpers
    from services.category_vendor_profile import normalize_category_id
    category_id = normalize_category_id(category) or category
    
    data = await catalog_controller.list_vendors(
        get_db_from_request(request),
        pagination,
        category_id=category_id,
        city=city,
        include_inactive=False,
    )
    
    await cache.set(cache_key, data, 600) # 10 minutes cache TTL
    
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Vendors fetched",
        request_id=_request_id(request),
    )


@router.get("/vendors/{vendor_id}/availability", response_model=ResponseEnvelope[dict[str, Any]])
async def get_vendor_availability(
    vendor_id: str,
    request: Request,
    month: Optional[str] = Query(default=None),
):
    from datetime import datetime
    from core.cache import get_cache_service
    cache = get_cache_service()
    
    current_month = month or datetime.now().strftime("%Y-%m")
    cache_key = f"availability:{vendor_id}:{current_month}"
    
    cached = await cache.get(cache_key)
    if cached:
        return ResponseEnvelope[dict[str, Any]](
            success=True,
            data=cached,
            message="Availability fetched (cached)",
            request_id=_request_id(request),
        )
        
    db = get_db_from_request(request)
    vendor = await db.vendors.find_one({"id": vendor_id})
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
        
    # Find bookings & active resource locks for this vendor
    bookings = await db.bookings.find(
        {
            "vendor_id": vendor_id,
            "status": {"$in": ["CONFIRMED", "PAYMENT_RECEIVED", "IN_PROGRESS"]},
        },
        {"_id": 0, "id": 1, "scheduled_at": 1, "status": 1}
    ).to_list(length=200)
    
    locks = await db.resource_locks.find(
        {
            "entity_id": vendor_id,
            "status": "ACTIVE",
        },
        {"_id": 0, "id": 1, "expires_at": 1}
    ).to_list(length=100)
    
    data = {
        "vendor_id": vendor_id,
        "month": current_month,
        "bookings": bookings,
        "locks": locks,
    }
    
    await cache.set(cache_key, data, 30) # 30 seconds TTL
    
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Availability fetched",
        request_id=_request_id(request),
    )


@router.get("/vendors/me", response_model=ResponseEnvelope[Optional[dict[str, Any]]])
async def get_my_vendor(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    data = await catalog_controller.get_my_vendor(get_db_from_request(request), current_user)
    return ResponseEnvelope[Optional[dict[str, Any]]](
        success=True,
        data=data,
        message="Vendor profile fetched",
        request_id=_request_id(request),
    )


@router.post("/vendors", response_model=ResponseEnvelope[dict[str, Any]])
async def create_vendor(
    payload: VendorCreate,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    data = await catalog_controller.create_vendor(get_db_from_request(request), payload, current_user)
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Vendor created",
        request_id=_request_id(request),
    )


@router.get("/vendors/{vendor_id}", response_model=ResponseEnvelope[dict[str, Any]])
async def get_vendor(vendor_id: str, request: Request):
    from core.cache import get_cache_service
    cache = get_cache_service()
    cache_key = f"vendor:{vendor_id}"
    
    cached = await cache.get(cache_key)
    if cached:
        return ResponseEnvelope[dict[str, Any]](
            success=True,
            data=cached,
            message="Vendor fetched (cached)",
            request_id=_request_id(request),
        )
        
    data = await catalog_controller.get_vendor(get_db_from_request(request), vendor_id)
    await cache.set(cache_key, data, 300) # 5 minutes TTL
    
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Vendor fetched",
        request_id=_request_id(request),
    )


@router.put("/vendors/{vendor_id}", response_model=ResponseEnvelope[dict[str, Any]])
async def update_vendor(
    vendor_id: str,
    payload: VendorPatch,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    data = await catalog_controller.update_vendor(db, vendor_id, payload, current_user)
    
    # Invalidate cache keys
    from core.cache import get_cache_service
    cache = get_cache_service()
    await cache.delete(f"vendor:{vendor_id}")
    await cache.delete(f"booking_flow:{vendor_id}")
    await cache.delete(f"packages:{vendor_id}")
    
    # Fetch vendor's city/category to invalidate list cache
    vendor = await db.vendors.find_one({"id": vendor_id}, {"city": 1, "category_id": 1})
    if vendor:
        city = vendor.get("city")
        cat = vendor.get("category_id")
        if city and cat:
            await cache.delete_pattern(f"vendor_list:{city.lower()}:{cat.lower()}:*")
            
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Vendor updated",
        request_id=_request_id(request),
    )


@router.put("/vendors/{vendor_id}/pricing-rules", response_model=ResponseEnvelope[dict[str, Any]])
async def update_vendor_pricing_rules(
    vendor_id: str,
    request: Request,
    rules: list[dict[str, Any]] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    data = await catalog_controller.update_vendor_pricing_rules(
        get_db_from_request(request),
        vendor_id,
        rules,
        current_user,
    )
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Vendor pricing rules updated",
        request_id=_request_id(request),
    )


@router.post("/vendors/{vendor_id}/media", response_model=ResponseEnvelope[dict[str, Any]])
async def add_vendor_media(
    vendor_id: str,
    payload: dict[str, Any],
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    data = await catalog_controller.add_vendor_media(get_db_from_request(request), vendor_id, payload, current_user)
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Vendor media added",
        request_id=_request_id(request),
    )


@router.put("/vendors/{vendor_id}/media/reorder", response_model=ResponseEnvelope[dict[str, Any]])
async def reorder_vendor_media(
    vendor_id: str,
    request: Request,
    payload: dict[str, list[str]] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    data = await catalog_controller.reorder_vendor_media(
        get_db_from_request(request),
        vendor_id,
        payload.get("media_order", []),
        current_user,
    )
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Vendor media reordered",
        request_id=_request_id(request),
    )


@router.get("/packages", response_model=ResponseEnvelope[dict[str, Any]])
async def list_packages(
    request: Request,
    pagination: Pagination = Depends(pagination_params),
    vendor_id: Optional[str] = None,
):
    from core.cache import get_cache_service
    cache = get_cache_service()
    cache_key = f"packages:{vendor_id}"
    
    if vendor_id:
        cached = await cache.get(cache_key)
        if cached:
            return ResponseEnvelope[dict[str, Any]](
                success=True,
                data=cached,
                message="Packages fetched (cached)",
                request_id=_request_id(request),
            )
            
    data = await catalog_controller.list_packages(get_db_from_request(request), pagination, vendor_id)
    if vendor_id:
        await cache.set(cache_key, data, 900) # 15 minutes TTL
        
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Packages fetched",
        request_id=_request_id(request),
    )


@router.post("/packages", response_model=ResponseEnvelope[dict[str, Any]])
async def create_package(
    payload: PackageCreate,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    data = await catalog_controller.create_package(db, payload, current_user)
    
    vendor_id = payload.vendor_id
    if vendor_id:
        from core.cache import get_cache_service
        cache = get_cache_service()
        await cache.delete(f"packages:{vendor_id}")
        
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Package created",
        request_id=_request_id(request),
    )


@router.get("/packages/{package_id}", response_model=ResponseEnvelope[dict[str, Any]])
async def get_package(package_id: str, request: Request):
    data = await catalog_controller.get_package(get_db_from_request(request), package_id)
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Package fetched",
        request_id=_request_id(request),
    )


@router.put("/packages/{package_id}", response_model=ResponseEnvelope[dict[str, Any]])
async def update_package(
    package_id: str,
    payload: PackagePatch,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db_from_request(request)
    data = await catalog_controller.update_package(db, package_id, payload, current_user)
    
    # Retrieve package to get vendor_id and invalidate cache
    package = await db.packages.find_one({"id": package_id})
    if package:
        vendor_id = package.get("vendor_id")
        if vendor_id:
            from core.cache import get_cache_service
            cache = get_cache_service()
            await cache.delete(f"packages:{vendor_id}")
            
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Package updated",
        request_id=_request_id(request),
    )


@router.post("/events", response_model=ResponseEnvelope[dict[str, Any]])
async def create_event(
    payload: EventCreate,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    data = await catalog_controller.create_event(get_db_from_request(request), payload, current_user)
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Event created",
        request_id=_request_id(request),
    )


@router.get("/events", response_model=ResponseEnvelope[dict[str, Any]])
async def list_events(
    request: Request,
    pagination: Pagination = Depends(pagination_params),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    data = await catalog_controller.list_events(get_db_from_request(request), pagination, current_user)
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Events fetched",
        request_id=_request_id(request),
    )


@router.get("/events/{event_id}", response_model=ResponseEnvelope[dict[str, Any]])
async def get_event(
    event_id: str,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    data = await catalog_controller.get_event(get_db_from_request(request), event_id, current_user)
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Event fetched",
        request_id=_request_id(request),
    )


@router.post("/quotes", response_model=ResponseEnvelope[dict[str, Any]])
async def create_quote(
    payload: QuoteCreate,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    data = await catalog_controller.create_quote(get_db_from_request(request), payload, current_user)
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Quote created",
        request_id=_request_id(request),
    )


@router.get("/quotes", response_model=ResponseEnvelope[dict[str, Any]])
async def list_quotes(
    request: Request,
    pagination: Pagination = Depends(pagination_params),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    data = await catalog_controller.list_quotes(get_db_from_request(request), pagination, current_user)
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Quotes fetched",
        request_id=_request_id(request),
    )


@router.put("/quotes/{quote_id}/respond", response_model=ResponseEnvelope[dict[str, Any]])
async def respond_quote(
    quote_id: str,
    payload: QuoteRespond,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    data = await catalog_controller.respond_quote(get_db_from_request(request), quote_id, payload, current_user)
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Quote response saved",
        request_id=_request_id(request),
    )


@router.post("/quotes/attachments", response_model=ResponseEnvelope[dict[str, Any]])
async def upload_quote_attachment(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    metadata = {
        "id": f"att_{file.filename or 'upload'}",
        "filename": file.filename,
        "content_type": file.content_type,
        "uploaded_by": str(current_user.get("id")),
    }
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=metadata,
        message="Attachment accepted",
        request_id=_request_id(request),
    )


@router.post("/reviews", response_model=ResponseEnvelope[dict[str, Any]])
async def create_review(
    payload: ReviewCreate,
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    data = await catalog_controller.create_review(get_db_from_request(request), payload, current_user)
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Review created",
        request_id=_request_id(request),
    )


@router.get("/reviews", response_model=ResponseEnvelope[dict[str, Any]])
async def list_reviews(
    request: Request,
    pagination: Pagination = Depends(pagination_params),
    vendor_id: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
):
    data = await catalog_controller.list_reviews(
        get_db_from_request(request),
        pagination,
        vendor_id=vendor_id,
        user_id=user_id,
    )
    return ResponseEnvelope[dict[str, Any]](
        success=True,
        data=data,
        message="Reviews fetched",
        request_id=_request_id(request),
    )
