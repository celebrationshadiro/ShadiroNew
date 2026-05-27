"""
Bookings router package.

Assembles the sub-routers so that `from routers.bookings import router`
continues to work exactly as before.

Route registration ORDER matters — more specific paths (e.g. /service/intent,
/rental/availability) must come before wildcard paths (e.g. /{booking_id}).
"""
from fastapi import APIRouter

from .intents import router as intents_router
from .service_bookings import router as service_router
from .rentals import router as rentals_router
from .actions import router as actions_router

router = APIRouter(prefix="/api/bookings", tags=["bookings"])

# Order matters: specific prefix routes first, wildcard routes last
router.include_router(intents_router)
router.include_router(service_router)
router.include_router(rentals_router)
router.include_router(actions_router)
