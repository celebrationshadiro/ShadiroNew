from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI, Request
import pymongo.errors
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, TEXT

# BUG 2 FIX: Move late import to top with graceful degradation
try:
    from shadiro_delivery_network.indexes import ensure_delivery_indexes
    _HAS_DELIVERY_NETWORK = True
except ImportError:
    _HAS_DELIVERY_NETWORK = False
    ensure_delivery_indexes = None

from core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class CollectionNames:
    USERS = "users"
    VENDORS = "vendors"
    CATEGORIES = "categories"
    PACKAGES = "packages"
    REVIEWS = "reviews"
    EVENTS = "events"
    QUOTES = "quotes"
    REFRESH_TOKENS = "refresh_tokens"
    REVOKED_TOKENS = "revoked_tokens"
    PASSWORD_RESET_TOKENS = "password_reset_tokens"
    VENDOR_CATEGORIES = "vendor_categories"
    SERVICE_DEFINITIONS = "service_definitions"
    BOOKING_INTENTS = "booking_intents"
    BOOKINGS = "bookings"
    PAYMENTS = "payments"
    WEBHOOK_EVENTS = "webhook_events"
    RESOURCE_LOCKS = "resource_locks"
    STATE_TRANSITIONS = "state_transitions"
    VENDOR_LEDGER = "vendor_ledger"
    PAYOUTS = "payouts"
    REFUNDS = "refunds"
    GROCERY_ITEMS = "grocery_items"
    GROCERY_ORDERS = "grocery_orders"
    NOTIFICATIONS = "notifications"
    ADMIN_AUDIT_LOGS = "admin_audit_logs"
    AUDIT_LOGS = "audit_logs"
    PLATFORM_CONFIG = "platform_config"
    # BUG 5 FIX: Add missing grocery collections to Constants
    GROCERY_PRODUCTS = "grocery_products"
    GROCERY_VENDOR_PROFILES = "grocery_vendor_profiles"


class MongoDatabaseManager:
    """Canonical Mongo manager for the unified marketplace architecture."""

    def __init__(
        self,
        mongo_url: str,
        db_name: str,
        *,
        min_pool_size: int = 5,
        max_pool_size: int = 100,
        server_selection_timeout_ms: int = 5000,
    ):
        self.mongo_url = mongo_url
        self.db_name = db_name
        self.min_pool_size = 10
        self.max_pool_size = 50
        self.server_selection_timeout_ms = 5000
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        if self.client is not None and self.db is not None:
            return
        self.client = AsyncIOMotorClient(
            self.mongo_url,
            minPoolSize=self.min_pool_size,
            maxPoolSize=self.max_pool_size,
            maxIdleTimeMS=30000,
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=self.server_selection_timeout_ms,
            w="majority",
            readPreference="secondaryPreferred",
            uuidRepresentation="standard",
        )
        self.db = self.client[self.db_name]
        logger.info("mongo_connected", extra={"event": "mongo_connected", "db_name": self.db_name, "pool": "10-50", "readPreference": "secondaryPreferred", "writeConcern": "majority"})

    async def close(self) -> None:
        if self.client is None:
            return
        self.client.close()
        self.client = None
        self.db = None
        logger.info("mongo_closed", extra={"event": "mongo_closed"})

    def _require_db(self) -> AsyncIOMotorDatabase:
        if self.db is None:
            raise RuntimeError("MongoDB is not connected")
        return self.db

    def collection(self, name: str) -> AsyncIOMotorCollection:
        return self._require_db()[name]

    # Canonical collection getters
    def users(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.USERS)

    def vendors(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.VENDORS)

    def vendor_categories(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.VENDOR_CATEGORIES)

    def categories(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.CATEGORIES)

    def packages(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.PACKAGES)

    def reviews(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.REVIEWS)

    def booking_intents(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.BOOKING_INTENTS)

    def bookings(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.BOOKINGS)

    def payments(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.PAYMENTS)

    def resource_locks(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.RESOURCE_LOCKS)

    def state_transitions(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.STATE_TRANSITIONS)

    def vendor_ledger(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.VENDOR_LEDGER)

    def payouts(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.PAYOUTS)

    def refunds(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.REFUNDS)

    def grocery_items(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.GROCERY_ITEMS)

    def grocery_orders(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.GROCERY_ORDERS)

    # BUG 3 FIX: Missing collection getters added
    def notifications(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.NOTIFICATIONS)

    def admin_audit_logs(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.ADMIN_AUDIT_LOGS)

    def audit_logs(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.AUDIT_LOGS)

    def platform_config(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.PLATFORM_CONFIG)

    def service_definitions(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.SERVICE_DEFINITIONS)

    def webhook_events(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.WEBHOOK_EVENTS)

    def revoked_tokens(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.REVOKED_TOKENS)

    def refresh_tokens(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.REFRESH_TOKENS)

    def password_reset_tokens(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.PASSWORD_RESET_TOKENS)

    def grocery_products(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.GROCERY_PRODUCTS)

    def grocery_vendor_profiles(self) -> AsyncIOMotorCollection:
        return self.collection(CollectionNames.GROCERY_VENDOR_PROFILES)

    async def ensure_indexes(self) -> None:
        """Create all canonical unique/query/TTL/text indexes."""
        _raw_db = self._require_db()

        class SafeCollectionWrapper:
            def __init__(self, collection):
                self._collection = collection

            async def create_index(self, keys, **kwargs):
                # All index names are preserved exactly as passed.
                # No stripping. The OperationFailure handler below is sufficient.
                try:
                    return await self._collection.create_index(keys, **kwargs)
                except pymongo.errors.OperationFailure as e:
                    if e.code == 85 or "already exists with different options" in str(e):
                        logger.warning(
                            "IndexOptionsConflict on '%s' for keys %s: %s",
                            self._collection.name, keys, str(e)
                        )
                    else:
                        raise

        class SafeDatabaseWrapper:
            def __getitem__(self, name: str) -> SafeCollectionWrapper:
                return SafeCollectionWrapper(_raw_db[name])

        db = SafeDatabaseWrapper()

        async def ensure_webhook_event_id_unique_index() -> None:
            collection = _raw_db[CollectionNames.WEBHOOK_EVENTS]
            index_name = "uniq_webhook_events_event_id"
            keys = [("event_id", ASCENDING)]

            def index_matches_required_options(index_info: dict) -> bool:
                return (
                    index_info.get("key") == keys
                    and index_info.get("unique") is True
                    and index_info.get("sparse") is not True
                )

            existing_index = (await collection.index_information()).get(index_name)
            if existing_index and not index_matches_required_options(existing_index):
                logger.warning(
                    "Dropping webhook event index '%s' to recreate it with required unique options.",
                    index_name,
                )
                await collection.drop_index(index_name)

            try:
                await collection.create_index(
                    keys,
                    unique=True,
                    name=index_name,
                )
            except pymongo.errors.OperationFailure as e:
                if e.code == 85 or "already exists with different options" in str(e):
                    logger.warning(
                        "IndexOptionsConflict on '%s': %s. Recreating index.",
                        index_name,
                        str(e),
                    )
                    existing_index = (await collection.index_information()).get(index_name)
                    if existing_index:
                        await collection.drop_index(index_name)
                    await collection.create_index(
                        keys,
                        unique=True,
                        name=index_name,
                    )
                else:
                    raise

        # BUG 4 FIX: Added Try/Except and progress logging
        try:
            logger.info("Starting index creation for all collections...")
            
            logger.info("Creating unique indexes...")
            await db[CollectionNames.USERS].create_index(
                [("id", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_users_id",
            )
            await db[CollectionNames.USERS].create_index(
                [("email", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_users_email",
            )
            await db[CollectionNames.USERS].create_index(
                [("phone", ASCENDING)],
                unique=True,
                partialFilterExpression={"phone": {"$type": "string"}},
                name="uniq_users_phone",
            )
            await db[CollectionNames.VENDORS].create_index(
                [("id", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_vendors_id",
            )
            await db[CollectionNames.VENDORS].create_index(
                [("user_id", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_vendors_user_id",
            )
            await db[CollectionNames.CATEGORIES].create_index(
                [("slug", ASCENDING)],
                unique=True,
                name="uniq_categories_slug",
            )
            await db[CollectionNames.CATEGORIES].create_index(
                [("id", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_categories_id",
            )
            await db[CollectionNames.PACKAGES].create_index(
                [("id", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_packages_id",
            )
            await db[CollectionNames.REVIEWS].create_index(
                [("id", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_reviews_id",
            )
            await db[CollectionNames.REVIEWS].create_index(
                [("user_id", ASCENDING), ("vendor_id", ASCENDING), ("order_id", ASCENDING)],
                unique=True,
                partialFilterExpression={"order_id": {"$type": "string"}},
                name="uniq_reviews_user_vendor_order",
            )
            await db[CollectionNames.EVENTS].create_index(
                [("id", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_events_id",
            )
            await db[CollectionNames.QUOTES].create_index(
                [("id", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_quotes_id",
            )
            await db[CollectionNames.REFRESH_TOKENS].create_index(
                [("jti", ASCENDING)],
                unique=True,
                name="uniq_refresh_tokens_jti",
            )
            await db[CollectionNames.REFRESH_TOKENS].create_index(
                [("token_hash", ASCENDING)],
                unique=True,
                name="uniq_refresh_tokens_hash",
            )
            await db[CollectionNames.REVOKED_TOKENS].create_index(
                [("jti", ASCENDING)],
                unique=True,
                name="uniq_revoked_tokens_jti",
            )
            await db[CollectionNames.BOOKINGS].create_index(
                [("id", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_bookings_id",
            )
            await db[CollectionNames.BOOKING_INTENTS].create_index(
                [("id", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_booking_intents_id",
            )
            await db[CollectionNames.BOOKING_INTENTS].create_index(
                [("idempotency_key", ASCENDING)],
                unique=True,
                name="uniq_booking_intents_idempotency_key",
            )
            await db[CollectionNames.PAYMENTS].create_index(
                [("id", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_payments_id",
            )
            await db[CollectionNames.PAYMENTS].create_index(
                [("booking_intent_id", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_payments_booking_intent_id",
            )
            await db[CollectionNames.PAYMENTS].create_index(
                [("razorpay_order_id", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_payments_razorpay_order_id",
            )
            await db[CollectionNames.PAYMENTS].create_index(
                [("razorpay_payment_id", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_payments_razorpay_payment_id",
            )
            await db[CollectionNames.PAYMENTS].create_index(
                [("idempotency_key", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_payments_idempotency_key",
            )
            await ensure_webhook_event_id_unique_index()
            await db[CollectionNames.PAYOUTS].create_index(
                [("idempotency_key", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_payouts_idempotency_key",
            )
            await db[CollectionNames.RESOURCE_LOCKS].create_index(
                [("id", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_resource_locks_id",
            )
            await db[CollectionNames.PAYOUTS].create_index(
                [("id", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_payouts_id",
            )
            await db[CollectionNames.REFUNDS].create_index(
                [("id", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_refunds_id",
            )
            await db[CollectionNames.RESOURCE_LOCKS].create_index(
                [("entity_id", ASCENDING), ("entity_type", ASCENDING)],
                unique=True,
                partialFilterExpression={"status": "ACTIVE"},
                name="uniq_active_resource_lock_entity",
            )

            logger.info("Creating query indexes...")
            await db[CollectionNames.BOOKINGS].create_index(
                [("customer_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)],
                name="idx_bookings_customer_status_created",
            )
            await db[CollectionNames.BOOKINGS].create_index(
                [("user_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)],
                name="idx_bookings_user_status_created_v2",
            )
            await db[CollectionNames.BOOKINGS].create_index(
                [("vendor_id", ASCENDING), ("event_date", ASCENDING), ("status", ASCENDING)],
                name="idx_bookings_vendor_event_date_status",
            )
            await db[CollectionNames.BOOKINGS].create_index(
                [("intent_id", ASCENDING)],
                unique=True,
                sparse=True,
                name="uniq_bookings_intent_id_v2",
            )
            await db[CollectionNames.BOOKINGS].create_index(
                [("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="idx_bookings_user_date",
            )
            await db[CollectionNames.USERS].create_index(
                [("role", ASCENDING), ("is_active", ASCENDING), ("created_at", DESCENDING)],
                name="idx_users_role_active_created",
            )
            await db[CollectionNames.VENDORS].create_index(
                [
                    ("category", ASCENDING),
                    ("category_id", ASCENDING),
                    ("city", ASCENDING),
                    ("is_active", ASCENDING),
                    ("rating", DESCENDING),
                    ("avg_rating", DESCENDING),
                ],
                name="idx_vendors_category_city_active_rating",
            )
            await db[CollectionNames.VENDORS].create_index(
                [("city", ASCENDING), ("is_active", ASCENDING)],
                name="idx_vendors_city_active_v2",
            )
            await db[CollectionNames.VENDORS].create_index(
                [("location", "2dsphere")],
                name="idx_vendors_location_geo",
                partialFilterExpression={"location": {"$type": "object"}}
            )
            await db[CollectionNames.VENDORS].create_index(
                [("category_id", ASCENDING), ("status", ASCENDING), ("city", ASCENDING)],
                name="idx_vendors_category_status_city",
            )
            await db[CollectionNames.VENDORS].create_index(
                [("is_featured", ASCENDING), ("rating", DESCENDING)],
                name="idx_vendors_featured_rating",
            )
            await db[CollectionNames.CATEGORIES].create_index(
                [("is_active", ASCENDING), ("sort_order", ASCENDING), ("name", ASCENDING)],
                name="idx_categories_active_sort",
            )
            await db[CollectionNames.PACKAGES].create_index(
                [("vendor_id", ASCENDING), ("is_active", ASCENDING), ("tier", ASCENDING)],
                name="idx_packages_vendor_active_tier",
            )
            await db[CollectionNames.PACKAGES].create_index(
                [("price", ASCENDING), ("is_active", ASCENDING)],
                name="idx_packages_price_active",
            )
            await db[CollectionNames.REVIEWS].create_index(
                [("vendor_id", ASCENDING), ("created_at", DESCENDING)],
                name="idx_reviews_vendor_created",
            )
            await db[CollectionNames.REVIEWS].create_index(
                [("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="idx_reviews_user_created",
            )
            await db[CollectionNames.EVENTS].create_index(
                [("user_id", ASCENDING), ("date", DESCENDING)],
                name="idx_events_user_date",
            )
            await db[CollectionNames.QUOTES].create_index(
                [("customer_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)],
                name="idx_quotes_customer_status_created",
            )
            await db[CollectionNames.QUOTES].create_index(
                [("user_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)],
                name="idx_quotes_user_status_created_v2",
            )
            await db[CollectionNames.QUOTES].create_index(
                [("vendor_id", ASCENDING), ("status", ASCENDING)],
                name="idx_quotes_vendor_status_v2",
            )
            await db[CollectionNames.QUOTES].create_index(
                [("status", ASCENDING), ("created_at", DESCENDING)],
                name="idx_quotes_status_created_v2",
            )
            await db[CollectionNames.QUOTES].create_index(
                [("user_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)],
                name="idx_quotes_user_status_created",
            )
            await db[CollectionNames.QUOTES].create_index(
                [("vendor_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)],
                name="idx_quotes_vendor_status_created",
            )
            await db[CollectionNames.REFRESH_TOKENS].create_index(
                [("user_id", ASCENDING), ("family_id", ASCENDING), ("revoked_at", ASCENDING)],
                name="idx_refresh_tokens_user_family_revoked",
            )
            await db[CollectionNames.SERVICE_DEFINITIONS].create_index(
                [("vendor_id", ASCENDING)],
                unique=True,
                name="uniq_service_definitions_vendor_id",
            )
            await db[CollectionNames.BOOKINGS].create_index(
                [("vendor_id", ASCENDING), ("status", ASCENDING)],
                name="idx_bookings_vendor_status",
            )
            await db[CollectionNames.BOOKINGS].create_index(
                [("status", ASCENDING), ("created_at", DESCENDING)],
                name="idx_bookings_status_date",
            )
            await db[CollectionNames.BOOKINGS].create_index(
                [("user_id", ASCENDING), ("status", ASCENDING)],
                name="idx_bookings_user_status",
            )
            await db[CollectionNames.BOOKINGS].create_index(
                [("category_type", ASCENDING), ("status", ASCENDING)],
                name="idx_bookings_category_status",
            )
            await db[CollectionNames.BOOKING_INTENTS].create_index(
                [("user_id", ASCENDING), ("status", ASCENDING)],
                name="idx_booking_intents_user_status",
            )
            await db[CollectionNames.VENDOR_LEDGER].create_index(
                [("vendor_id", ASCENDING), ("created_at", DESCENDING)],
                name="idx_ledger_vendor_date",
            )
            await db[CollectionNames.STATE_TRANSITIONS].create_index(
                [("entity_id", ASCENDING), ("created_at", ASCENDING)],
                name="idx_state_transitions_entity_created_at",
            )
            await db[CollectionNames.PAYMENTS].create_index(
                [("status", ASCENDING), ("created_at", DESCENDING)],
                name="idx_payments_status_date",
            )
            await db[CollectionNames.PAYOUTS].create_index(
                [("vendor_id", ASCENDING), ("status", ASCENDING)],
                name="idx_payouts_vendor_status",
            )
            await db[CollectionNames.PAYOUTS].create_index(
                [("vendor_id", ASCENDING), ("status", ASCENDING), ("created_at", ASCENDING)],
                name="idx_payouts_vendor_status_created_at",
            )
            await db[CollectionNames.REFUNDS].create_index(
                [("booking_id", ASCENDING), ("status", ASCENDING), ("created_at", ASCENDING)],
                name="idx_refunds_booking_status_created_at",
            )
            await db[CollectionNames.AUDIT_LOGS].create_index(
                [("created_at", ASCENDING)],
                name="idx_audit_logs_created_at",
            )
            await db[CollectionNames.ADMIN_AUDIT_LOGS].create_index(
                [("admin_id", ASCENDING), ("created_at", ASCENDING)],
                name="idx_admin_audit_logs_admin_created_at",
            )
        
            logger.info("Creating grocery indexes...")
            # BUG 5 FIX: Replaced raw strings with CollectionNames
            await db[CollectionNames.GROCERY_PRODUCTS].create_index(
                [("vendor_id", ASCENDING), ("in_stock", ASCENDING)],
                name="idx_grocery_products_stock",
            )
            await db[CollectionNames.GROCERY_PRODUCTS].create_index(
                [("vendor_id", ASCENDING), ("category", ASCENDING)],
                name="idx_grocery_products_cat",
            )
            await db[CollectionNames.GROCERY_VENDOR_PROFILES].create_index(
                [("vendor_id", ASCENDING)],
                unique=True,
                name="uniq_grocery_profile",
            )
            await db[CollectionNames.GROCERY_VENDOR_PROFILES].create_index(
                [("city", ASCENDING), ("area", ASCENDING)],
                name="idx_grocery_profile_location",
            )
            await db[CollectionNames.GROCERY_VENDOR_PROFILES].create_index(
                [("pincode", ASCENDING)],
                name="idx_grocery_profile_pincode",
            )
            await db[CollectionNames.GROCERY_ORDERS].create_index(
                [("idempotency_key", ASCENDING)],
                unique=True,
                name="uniq_grocery_order_idem",
            )
            await db[CollectionNames.GROCERY_ORDERS].create_index(
                [("customer_id", ASCENDING), ("created_at", DESCENDING)],
                name="idx_grocery_orders_customer",
            )
            await db[CollectionNames.GROCERY_ORDERS].create_index(
                [("vendor_id", ASCENDING), ("status", ASCENDING)],
                name="idx_grocery_orders_vendor_status",
            )
 
            logger.info("Creating RESOURCE_LOCKS indexes for query optimization...")
            await db[CollectionNames.RESOURCE_LOCKS].create_index(
                [("vendor_id", ASCENDING), ("date", ASCENDING), ("status", ASCENDING)],
                name="idx_locks_vendor_date_status",
            )
            await db[CollectionNames.RESOURCE_LOCKS].create_index(
                [("vendor_id", ASCENDING), ("date_value", ASCENDING), ("status", ASCENDING)],
                name="idx_locks_vendor_date_value_status",
            )
 
            logger.info("Creating TTL indexes...")
            await db[CollectionNames.RESOURCE_LOCKS].create_index(
                [("expires_at", ASCENDING)],
                expireAfterSeconds=0,
                name="ttl_resource_locks_expires_at",
            )
            await db[CollectionNames.BOOKING_INTENTS].create_index(
                [("expires_at", ASCENDING)],
                expireAfterSeconds=0,
                name="ttl_booking_intents_expires_at",
            )
            await db[CollectionNames.WEBHOOK_EVENTS].create_index(
                [("received_at", ASCENDING)],
                expireAfterSeconds=2592000,
                name="ttl_webhook_30d",
            )
            await db[CollectionNames.REFRESH_TOKENS].create_index(
                [("expires_at", ASCENDING)],
                expireAfterSeconds=0,
                name="ttl_refresh_tokens_expires_at",
            )
            await db[CollectionNames.REVOKED_TOKENS].create_index(
                [("expires_at", ASCENDING)],
                expireAfterSeconds=0,
                name="ttl_revoked_tokens_expires_at",
            )
            await db[CollectionNames.PASSWORD_RESET_TOKENS].create_index(
                [("expires_at", ASCENDING)],
                expireAfterSeconds=0,
                name="ttl_password_reset_tokens_expires_at",
            )
            await db[CollectionNames.PASSWORD_RESET_TOKENS].create_index(
                [("token_hash", ASCENDING)],
                unique=True,
                name="uniq_password_reset_tokens_hash",
            )
            await db[CollectionNames.QUOTES].create_index(
                [("created_at", ASCENDING)],
                expireAfterSeconds=604800,
                name="ttl_quotes_created_at",
            )
 
            logger.info("Creating text indexes...")
            try:
                await _raw_db[CollectionNames.VENDORS].drop_index("txt_vendors_search")
            except Exception:
                pass
            await db[CollectionNames.VENDORS].create_index(
                [
                    ("business_name", TEXT),
                    ("name", TEXT),
                    ("description", TEXT),
                    ("category_id", TEXT),
                    ("tags", TEXT),
                ],
                name="txt_vendors_search",
                default_language="english",
            )
            await db[CollectionNames.GROCERY_ITEMS].create_index(
                [
                    ("name", TEXT),
                    ("description", TEXT),
                ],
                name="txt_grocery_items_search",
                default_language="english",
            )
            await db[CollectionNames.PACKAGES].create_index(
                [
                    ("name", TEXT),
                    ("description", TEXT),
                    ("services_included", TEXT),
                ],
                name="txt_packages_search",
                default_language="english",
            )

            if _HAS_DELIVERY_NETWORK and ensure_delivery_indexes:
                logger.info("Creating delivery network indexes...")
                await ensure_delivery_indexes(_raw_db)
            else:
                logger.warning("Delivery module not found; skipping delivery indexes.")
            logger.info("mongo_indexes_ensured", extra={"event": "mongo_indexes_ensured"})
        except Exception as e:
            logger.error("Failed to ensure indexes during startup: %s", str(e), exc_info=True)
            raise


def build_mongo_manager(settings: Optional[Settings] = None) -> MongoDatabaseManager:
    s = settings or get_settings()
    return MongoDatabaseManager(
        mongo_url=s.MONGO_URL,
        db_name=s.DB_NAME,
        min_pool_size=s.MONGO_MIN_POOL_SIZE,
        max_pool_size=s.MONGO_MAX_POOL_SIZE,
        server_selection_timeout_ms=s.MONGO_SERVER_SELECTION_TIMEOUT_MS,
    )


async def init_database(app: FastAPI, settings: Optional[Settings] = None) -> MongoDatabaseManager:
    """
    Initialize DB and attach manager + db instance to app.state.
    """
    manager = build_mongo_manager(settings)
    await manager.connect()
    await manager.ensure_indexes()
    app.state.mongo_manager = manager
    app.state.db = manager.db
    return manager


async def close_database(app: FastAPI) -> None:
    manager: Optional[MongoDatabaseManager] = getattr(app.state, "mongo_manager", None)
    if manager:
        await manager.close()


def get_db_from_request(request: Request) -> AsyncIOMotorDatabase:
    db = getattr(request.app.state, "db", None)
    if db is None:
        raise RuntimeError("Database is not initialized on app.state")
    return db
