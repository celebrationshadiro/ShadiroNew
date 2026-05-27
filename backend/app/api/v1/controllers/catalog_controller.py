from __future__ import annotations

from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

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
from app.api.v1.services import catalog_service


class CatalogController:
    async def list_categories(self, db: AsyncIOMotorDatabase) -> list[dict[str, Any]]:
        return await catalog_service.list_categories(db)

    async def upsert_category(self, db: AsyncIOMotorDatabase, payload: CategoryUpsert, current_user: dict[str, Any]):
        return await catalog_service.upsert_category(db, payload, current_user)

    async def list_vendors(
        self,
        db: AsyncIOMotorDatabase,
        pagination: Pagination,
        *,
        category_id: Optional[str],
        city: Optional[str],
        q: Optional[str],
        cursor: Optional[str] = None,
        include_inactive: bool,
    ):
        return await catalog_service.list_vendors(
            db,
            pagination,
            category_id=category_id,
            city=city,
            q=q,
            cursor=cursor,
            include_inactive=include_inactive,
        )

    async def get_vendor(self, db: AsyncIOMotorDatabase, vendor_id: str):
        return await catalog_service.get_vendor(db, vendor_id)

    async def get_my_vendor(self, db: AsyncIOMotorDatabase, current_user: dict[str, Any]):
        return await catalog_service.get_my_vendor(db, current_user)

    async def create_vendor(self, db: AsyncIOMotorDatabase, payload: VendorCreate, current_user: dict[str, Any]):
        return await catalog_service.create_vendor(db, payload, current_user)

    async def update_vendor(self, db: AsyncIOMotorDatabase, vendor_id: str, payload: VendorPatch, current_user: dict[str, Any]):
        return await catalog_service.update_vendor(db, vendor_id, payload, current_user)

    async def update_vendor_pricing_rules(
        self,
        db: AsyncIOMotorDatabase,
        vendor_id: str,
        rules: list[dict[str, Any]],
        current_user: dict[str, Any],
    ):
        return await catalog_service.update_vendor_pricing_rules(db, vendor_id, rules, current_user)

    async def add_vendor_media(
        self,
        db: AsyncIOMotorDatabase,
        vendor_id: str,
        payload: dict[str, Any],
        current_user: dict[str, Any],
    ):
        return await catalog_service.add_vendor_media(db, vendor_id, payload, current_user)

    async def reorder_vendor_media(
        self,
        db: AsyncIOMotorDatabase,
        vendor_id: str,
        media_order: list[str],
        current_user: dict[str, Any],
    ):
        return await catalog_service.reorder_vendor_media(db, vendor_id, media_order, current_user)

    async def list_packages(self, db: AsyncIOMotorDatabase, pagination: Pagination, vendor_id: Optional[str]):
        return await catalog_service.list_packages(db, pagination, vendor_id=vendor_id)

    async def get_package(self, db: AsyncIOMotorDatabase, package_id: str):
        return await catalog_service.get_package(db, package_id)

    async def create_package(self, db: AsyncIOMotorDatabase, payload: PackageCreate, current_user: dict[str, Any]):
        return await catalog_service.create_package(db, payload, current_user)

    async def update_package(
        self,
        db: AsyncIOMotorDatabase,
        package_id: str,
        payload: PackagePatch,
        current_user: dict[str, Any],
    ):
        return await catalog_service.update_package(db, package_id, payload, current_user)

    async def create_event(self, db: AsyncIOMotorDatabase, payload: EventCreate, current_user: dict[str, Any]):
        return await catalog_service.create_event(db, payload, current_user)

    async def list_events(self, db: AsyncIOMotorDatabase, pagination: Pagination, current_user: dict[str, Any]):
        return await catalog_service.list_events(db, pagination, current_user)

    async def get_event(self, db: AsyncIOMotorDatabase, event_id: str, current_user: dict[str, Any]):
        return await catalog_service.get_event(db, event_id, current_user)

    async def create_quote(self, db: AsyncIOMotorDatabase, payload: QuoteCreate, current_user: dict[str, Any]):
        return await catalog_service.create_quote(db, payload, current_user)

    async def list_quotes(self, db: AsyncIOMotorDatabase, pagination: Pagination, current_user: dict[str, Any]):
        return await catalog_service.list_quotes(db, pagination, current_user)

    async def respond_quote(
        self,
        db: AsyncIOMotorDatabase,
        quote_id: str,
        payload: QuoteRespond,
        current_user: dict[str, Any],
    ):
        return await catalog_service.respond_quote(db, quote_id, payload, current_user)

    async def create_review(self, db: AsyncIOMotorDatabase, payload: ReviewCreate, current_user: dict[str, Any]):
        return await catalog_service.create_review(db, payload, current_user)

    async def list_reviews(
        self,
        db: AsyncIOMotorDatabase,
        pagination: Pagination,
        *,
        vendor_id: Optional[str],
        user_id: Optional[str],
    ):
        return await catalog_service.list_reviews(db, pagination, vendor_id=vendor_id, user_id=user_id)


catalog_controller = CatalogController()
