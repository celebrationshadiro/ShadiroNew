from __future__ import annotations

from enum import Enum
from typing import Dict, Set


class CategoryType(str, Enum):
    SERVICE = "service"
    GROCERY = "grocery"
    RENTAL = "rental"


class BookingStatus(str, Enum):
    INTENT_CREATED = "intent_created"
    AWAITING_PAYMENT = "awaiting_payment"
    PAYMENT_PENDING_VERIFICATION = "payment_pending_verification"
    TOKEN_PAID = "token_paid"
    VENDOR_PENDING = "vendor_pending"
    VENDOR_ACCEPTED = "vendor_accepted"
    VENDOR_COUNTERED = "vendor_countered"
    VENDOR_REJECTED = "vendor_rejected"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAYOUT_PENDING = "payout_pending"
    PAYOUT_RELEASED = "payout_released"
    CANCELLED = "cancelled"
    REFUND_PENDING = "refund_pending"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class ActorRole(str, Enum):
    USER = "user"
    VENDOR = "vendor"
    ADMIN = "admin"
    SYSTEM = "system"


ACTIVE_LOCK_STATES: Set[str] = {"soft_locked", "hard_locked"}


CATEGORY_ACCEPTANCE_REQUIRED: Dict[CategoryType, bool] = {
    CategoryType.SERVICE: True,
    CategoryType.GROCERY: False,
    CategoryType.RENTAL: True,
}


CATEGORY_ESCROW_ENABLED: Dict[CategoryType, bool] = {
    CategoryType.SERVICE: True,
    CategoryType.GROCERY: False,
    CategoryType.RENTAL: False,
}


CATEGORY_SETTLEMENT_MODE: Dict[CategoryType, str] = {
    CategoryType.SERVICE: "escrow",
    CategoryType.GROCERY: "direct",
    CategoryType.RENTAL: "deposit_hold",
}
