from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase

from booking_engine.handlers.base_handler import BaseBookingHandler
from booking_engine.handlers.grocery_handler import GroceryBookingHandler
from booking_engine.handlers.rental_handler import RentalBookingHandler
from booking_engine.handlers.service_handler import ServiceBookingHandler
from booking_engine.models.booking_models import CategoryType


def build_handler_registry(db: AsyncIOMotorDatabase) -> dict[CategoryType, BaseBookingHandler]:
    return {
        CategoryType.SERVICE: ServiceBookingHandler(db),
        CategoryType.GROCERY: GroceryBookingHandler(db),
        CategoryType.RENTAL: RentalBookingHandler(db),
    }
