from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes.catalog import router as catalog_router
from routers.admin import router as admin_router
from routers.assistant import router as assistant_router
from routers.auth import router as auth_router
from routers.automation import router as automation_router
from routers.booking_flows import router as booking_flows_router
from routers.booking_risk import router as booking_risk_router
from routers.bookings import router as bookings_router
from routers.delivery_network import router as delivery_network_router
from routers.disputes import router as disputes_router
from routers.grocery import router as grocery_router
from routers.notifications import router as notifications_router
from routers.payments import router as payments_router
from routers.pricing import router as pricing_router
from routers.recommendations import router as recommendations_router
from routers.services import router as services_router
from routers.vendor_onboarding import router as vendor_onboarding_router
from routers.vendor_registration import router as vendor_registration_router
from routers.vendor_verification import router as vendor_verification_router
from routers.grocery_payments import router as grocery_payments_router
from routers.grocery_vendor import router as grocery_vendor_router

api_router = APIRouter()

for router in (
    auth_router,
    catalog_router,
    vendor_registration_router,
    admin_router,
    bookings_router,
    payments_router,
    notifications_router,
    services_router,
    grocery_router,
    recommendations_router,
    assistant_router,
    vendor_onboarding_router,
    pricing_router,
    automation_router,
    vendor_verification_router,
    disputes_router,
    booking_risk_router,
    booking_flows_router,
    delivery_network_router,
    grocery_payments_router,
    grocery_vendor_router,
):
    api_router.include_router(router)

