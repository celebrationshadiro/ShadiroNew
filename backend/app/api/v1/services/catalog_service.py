from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.api.v1.dependencies.pagination import Pagination
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
from app.api.v1.utils.documents import clean_update, public_doc
from canonical_models.common import UserRole, utcnow


DEFAULT_CATEGORIES = [
    {"id": "cat_photography", "name": "Photography", "slug": "photography", "is_active": True, "sort_order": 10},
    {"id": "cat_catering", "name": "Catering", "slug": "catering", "is_active": True, "sort_order": 20},
    {"id": "cat_decoration", "name": "Decoration", "slug": "decoration", "is_active": True, "sort_order": 30},
    {"id": "cat_makeup", "name": "Makeup", "slug": "makeup", "is_active": True, "sort_order": 40},
    {"id": "cat_dj", "name": "DJ", "slug": "dj", "is_active": True, "sort_order": 50},
    {"id": "cat_venue", "name": "Venue", "slug": "venue", "is_active": True, "sort_order": 60},
    {"id": "cat_grocery", "name": "Grocery", "slug": "grocery", "is_active": True, "sort_order": 70},
]


def _role(current_user: dict[str, Any] | None) -> str:
    raw = str((current_user or {}).get("role") or "").lower()
    return UserRole.CUSTOMER.value if raw == "user" else raw


def _user_id(current_user: dict[str, Any] | None) -> str:
    return str((current_user or {}).get("id") or (current_user or {}).get("sub") or "")


def _is_admin(current_user: dict[str, Any] | None) -> bool:
    return _role(current_user) == UserRole.ADMIN.value


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


async def _paginate(
    db: AsyncIOMotorDatabase,
    collection_name: str,
    query: dict[str, Any],
    pagination: Pagination,
    *,
    sort: list[tuple[str, int]],
    projection: Optional[dict[str, int]] = None,
) -> dict[str, Any]:
    limit = min(pagination.limit, 50)
    total = await db[collection_name].count_documents(query)
    cursor = db[collection_name].find(query, projection or {"_id": 0}).sort(sort).skip(pagination.skip).limit(limit)
    docs = [public_doc(doc) for doc in await cursor.to_list(length=limit)]
    return {
        "items": [doc for doc in docs if doc is not None],
        "total": total,
        "page": pagination.page,
        "page_size": limit,
        "has_next": pagination.skip + limit < total,
    }


async def _vendor_for_user(db: AsyncIOMotorDatabase, user_id: str) -> Optional[dict[str, Any]]:
    return await db.vendors.find_one({"user_id": user_id}, {"_id": 0})


async def _enforce_vendor_owner_or_admin(
    db: AsyncIOMotorDatabase,
    vendor_id: str,
    current_user: dict[str, Any],
) -> dict[str, Any]:
    vendor = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    if _is_admin(current_user):
        return vendor
    if str(vendor.get("user_id")) != _user_id(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vendor owner access required")
    return vendor


async def list_categories(db: AsyncIOMotorDatabase) -> list[dict[str, Any]]:
    docs = await db.categories.find({"is_active": {"$ne": False}}, {"_id": 0}).sort(
        [("sort_order", 1), ("name", 1)]
    ).to_list(length=500)
    if not docs:
        docs = await db.vendor_categories.find({}, {"_id": 0}).sort("name", 1).to_list(length=500)
    return [public_doc(doc) for doc in docs] or DEFAULT_CATEGORIES


async def upsert_category(
    db: AsyncIOMotorDatabase,
    payload: CategoryUpsert,
    current_user: dict[str, Any],
) -> dict[str, Any]:
    if not _is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    now = utcnow()
    doc = payload.model_dump()
    doc["updated_at"] = now
    updated = await db.categories.find_one_and_update(
        {"slug": payload.slug},
        {"$set": doc, "$setOnInsert": {"id": _new_id("cat"), "created_at": now}},
        projection={"_id": 0},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return public_doc(updated) or {}


async def list_vendors(
    db: AsyncIOMotorDatabase,
    pagination: Pagination,
    *,
    category_id: Optional[str] = None,
    city: Optional[str] = None,
    q: Optional[str] = None,
    cursor: Optional[str] = None,
    include_inactive: bool = False,
) -> dict[str, Any]:
    from bson.objectid import ObjectId
    from core.cache import get_cache_service

    query: dict[str, Any] = {}
    if not include_inactive:
        query["is_active"] = {"$ne": False}
        query["status"] = {"$nin": ["REJECTED", "SUSPENDED", "rejected", "suspended"]}
    if category_id:
        query["category_id"] = category_id
    if city:
        query["city"] = {"$regex": f"^{city}$", "$options": "i"}
    if q:
        query["$text"] = {"$search": q}

    # Retrieve total count from cache under production scale
    cache = get_cache_service()
    count_key = f"vendors_count:{city or 'all'}:{category_id or 'all'}"
    cached_count = await cache.get(count_key)
    if cached_count is not None:
        total_count = int(cached_count)
    else:
        total_count = await db.vendors.count_documents(query)
        await cache.set(count_key, total_count, 600)  # cache count for 10 mins

    limit = min(pagination.limit, 50)

    # Apply stable cursor-based query using _id
    if cursor:
        try:
            query["_id"] = {"$gt": ObjectId(cursor)}
        except Exception:
            pass

    cursor_obj = db.vendors.find(
        query,
        {"password_hash": 0, "hashed_password": 0}
    ).sort("_id", 1).limit(limit + 1)
    
    docs = await cursor_obj.to_list(length=limit + 1)
    has_more = len(docs) > limit
    vendors_list = docs[:limit]
    
    next_cursor = None
    if has_more and vendors_list:
        next_cursor = str(vendors_list[-1]["_id"])

    # Clean up ObjectIds for serialization
    cleaned_vendors = []
    for doc in vendors_list:
        p_doc = public_doc(doc)
        if p_doc:
            if "_id" in p_doc:
                p_doc["_id"] = str(p_doc["_id"])
            if "id" not in p_doc and "_id" in p_doc:
                p_doc["id"] = p_doc["_id"]
            cleaned_vendors.append(p_doc)

    return {
        "vendors": cleaned_vendors,
        "next_cursor": next_cursor,
        "has_more": has_more,
        "total_count": total_count
    }


async def get_vendor(db: AsyncIOMotorDatabase, vendor_id: str) -> dict[str, Any]:
    vendor = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    return public_doc(vendor) or {}


async def get_my_vendor(db: AsyncIOMotorDatabase, current_user: dict[str, Any]) -> dict[str, Any] | None:
    vendor = await _vendor_for_user(db, _user_id(current_user))
    return public_doc(vendor) if vendor else None


async def create_vendor(
    db: AsyncIOMotorDatabase,
    payload: VendorCreate,
    current_user: dict[str, Any],
) -> dict[str, Any]:
    user_id = _user_id(current_user)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    existing = await _vendor_for_user(db, user_id)
    if existing and not _is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vendor profile already exists")

    now = utcnow()
    doc = payload.model_dump()
    doc.update(
        {
            "id": _new_id("ven"),
            "user_id": user_id,
            "status": "PENDING",
            "subscription_plan": "free",
            "is_featured": False,
            "is_active": True,
            "rating": 0.0,
            "total_reviews": 0,
            "is_verified": False,
            "verification_status": "pending",
            "created_at": now,
            "updated_at": now,
        }
    )
    await db.vendors.insert_one(doc)
    return public_doc(doc) or {}


async def update_vendor(
    db: AsyncIOMotorDatabase,
    vendor_id: str,
    payload: VendorPatch,
    current_user: dict[str, Any],
) -> dict[str, Any]:
    await _enforce_vendor_owner_or_admin(db, vendor_id, current_user)
    update = clean_update(payload.model_dump(exclude_unset=True))
    if not update:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    update["updated_at"] = utcnow()
    updated = await db.vendors.find_one_and_update(
        {"id": vendor_id},
        {"$set": update},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    return public_doc(updated) or {}


async def update_vendor_pricing_rules(
    db: AsyncIOMotorDatabase,
    vendor_id: str,
    rules: list[dict[str, Any]],
    current_user: dict[str, Any],
) -> dict[str, Any]:
    await _enforce_vendor_owner_or_admin(db, vendor_id, current_user)
    updated = await db.vendors.find_one_and_update(
        {"id": vendor_id},
        {"$set": {"pricing_rules": rules, "updated_at": utcnow()}},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    return public_doc(updated) or {}


async def add_vendor_media(
    db: AsyncIOMotorDatabase,
    vendor_id: str,
    payload: dict[str, Any],
    current_user: dict[str, Any],
) -> dict[str, Any]:
    vendor = await _enforce_vendor_owner_or_admin(db, vendor_id, current_user)
    media = dict(payload)
    media.setdefault("id", _new_id("media"))
    media.setdefault("order", len(vendor.get("media") or []))
    updated = await db.vendors.find_one_and_update(
        {"id": vendor_id},
        {"$push": {"media": media}, "$set": {"updated_at": utcnow()}},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    return public_doc(updated) or {}


async def reorder_vendor_media(
    db: AsyncIOMotorDatabase,
    vendor_id: str,
    media_order: list[str],
    current_user: dict[str, Any],
) -> dict[str, Any]:
    vendor = await _enforce_vendor_owner_or_admin(db, vendor_id, current_user)
    order_map = {media_id: index for index, media_id in enumerate(media_order)}
    media = sorted(
        [{**item, "order": order_map.get(str(item.get("id")), item.get("order", 0))} for item in vendor.get("media", [])],
        key=lambda item: int(item.get("order", 0)),
    )
    updated = await db.vendors.find_one_and_update(
        {"id": vendor_id},
        {"$set": {"media": media, "updated_at": utcnow()}},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    return public_doc(updated) or {}


async def list_packages(
    db: AsyncIOMotorDatabase,
    pagination: Pagination,
    *,
    vendor_id: Optional[str] = None,
    active_only: bool = True,
) -> dict[str, Any]:
    query: dict[str, Any] = {}
    if vendor_id:
        query["vendor_id"] = vendor_id
    if active_only:
        query["is_active"] = {"$ne": False}
    return await _paginate(db, "packages", query, pagination, sort=[("price", 1), ("created_at", -1)])


async def get_package(db: AsyncIOMotorDatabase, package_id: str) -> dict[str, Any]:
    package = await db.packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
    return public_doc(package) or {}


async def create_package(
    db: AsyncIOMotorDatabase,
    payload: PackageCreate,
    current_user: dict[str, Any],
) -> dict[str, Any]:
    await _enforce_vendor_owner_or_admin(db, payload.vendor_id, current_user)
    now = utcnow()
    doc = payload.model_dump()
    doc.update({"id": _new_id("pkg"), "created_at": now, "updated_at": now})
    await db.packages.insert_one(doc)
    return public_doc(doc) or {}


async def update_package(
    db: AsyncIOMotorDatabase,
    package_id: str,
    payload: PackagePatch,
    current_user: dict[str, Any],
) -> dict[str, Any]:
    package = await db.packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
    await _enforce_vendor_owner_or_admin(db, str(package.get("vendor_id")), current_user)
    update = clean_update(payload.model_dump(exclude_unset=True))
    update["updated_at"] = utcnow()
    updated = await db.packages.find_one_and_update(
        {"id": package_id},
        {"$set": update},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    return public_doc(updated) or {}


async def create_event(
    db: AsyncIOMotorDatabase,
    payload: EventCreate,
    current_user: dict[str, Any],
) -> dict[str, Any]:
    now = utcnow()
    doc = payload.model_dump()
    doc.update({"id": _new_id("evt"), "user_id": _user_id(current_user), "is_active": True, "created_at": now})
    await db.events.insert_one(doc)
    return public_doc(doc) or {}


async def list_events(db: AsyncIOMotorDatabase, pagination: Pagination, current_user: dict[str, Any]) -> dict[str, Any]:
    query = {} if _is_admin(current_user) else {"user_id": _user_id(current_user)}
    return await _paginate(db, "events", query, pagination, sort=[("date", -1), ("created_at", -1)])


async def get_event(db: AsyncIOMotorDatabase, event_id: str, current_user: dict[str, Any]) -> dict[str, Any]:
    event = await db.events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if not _is_admin(current_user) and str(event.get("user_id")) != _user_id(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Event owner access required")
    return public_doc(event) or {}


async def create_quote(
    db: AsyncIOMotorDatabase,
    payload: QuoteCreate,
    current_user: dict[str, Any],
) -> dict[str, Any]:
    event = await db.events.find_one({"id": payload.event_id}, {"_id": 0, "user_id": 1})
    if event and not _is_admin(current_user) and str(event.get("user_id")) != _user_id(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Event owner access required")
    if not await db.vendors.find_one({"id": payload.vendor_id}, {"_id": 0, "id": 1}):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    now = utcnow()
    doc = payload.model_dump()
    doc.update({"id": _new_id("quo"), "user_id": _user_id(current_user), "status": "pending", "created_at": now})
    await db.quotes.insert_one(doc)
    return public_doc(doc) or {}


async def list_quotes(db: AsyncIOMotorDatabase, pagination: Pagination, current_user: dict[str, Any]) -> dict[str, Any]:
    query: dict[str, Any] = {}
    if _role(current_user) == UserRole.VENDOR.value:
        vendor = await _vendor_for_user(db, _user_id(current_user))
        query["vendor_id"] = str((vendor or {}).get("id") or "__none__")
    elif not _is_admin(current_user):
        query["user_id"] = _user_id(current_user)
    return await _paginate(db, "quotes", query, pagination, sort=[("created_at", -1)])


async def respond_quote(
    db: AsyncIOMotorDatabase,
    quote_id: str,
    payload: QuoteRespond,
    current_user: dict[str, Any],
) -> dict[str, Any]:
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")
    await _enforce_vendor_owner_or_admin(db, str(quote.get("vendor_id")), current_user)
    update = payload.model_dump()
    update.update({"status": "responded", "responded_at": utcnow()})
    updated = await db.quotes.find_one_and_update(
        {"id": quote_id},
        {"$set": update},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    return public_doc(updated) or {}


async def create_review(
    db: AsyncIOMotorDatabase,
    payload: ReviewCreate,
    current_user: dict[str, Any],
) -> dict[str, Any]:
    if not await db.vendors.find_one({"id": payload.vendor_id}, {"_id": 0, "id": 1}):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    now = utcnow()
    doc = payload.model_dump()
    doc.update({"id": _new_id("rev"), "user_id": _user_id(current_user), "created_at": now})
    try:
        await db.reviews.insert_one(doc)
    except DuplicateKeyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Review already exists") from exc
    await recompute_vendor_rating(db, payload.vendor_id)
    return public_doc(doc) or {}


async def list_reviews(
    db: AsyncIOMotorDatabase,
    pagination: Pagination,
    *,
    vendor_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> dict[str, Any]:
    query: dict[str, Any] = {}
    if vendor_id:
        query["vendor_id"] = vendor_id
    if user_id:
        query["user_id"] = user_id
    return await _paginate(db, "reviews", query, pagination, sort=[("created_at", -1)])


async def recompute_vendor_rating(db: AsyncIOMotorDatabase, vendor_id: str) -> None:
    agg = await db.reviews.aggregate(
        [
            {"$match": {"vendor_id": vendor_id}},
            {"$group": {"_id": "$vendor_id", "rating": {"$avg": "$rating"}, "total_reviews": {"$sum": 1}}},
        ]
    ).to_list(length=1)
    if not agg:
        return
    await db.vendors.update_one(
        {"id": vendor_id},
        {
            "$set": {
                "rating": round(float(agg[0].get("rating") or 0), 2),
                "total_reviews": int(agg[0].get("total_reviews") or 0),
                "updated_at": utcnow(),
            }
        },
    )
