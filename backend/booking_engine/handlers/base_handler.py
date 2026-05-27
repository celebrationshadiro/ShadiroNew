from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from motor.motor_asyncio import AsyncIOMotorDatabase

from booking_engine.models.booking_models import CategoryType


class BaseBookingHandler(ABC):
    category_type: CategoryType

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    @abstractmethod
    async def validate_create(self, payload: Dict[str, Any], current_user: Dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def reserve_resources(self, payload: Dict[str, Any], intent_id: str, ttl_seconds: int) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def release_resources(self, reservation: Dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def requires_vendor_acceptance(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def uses_escrow(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def payment_summary(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
