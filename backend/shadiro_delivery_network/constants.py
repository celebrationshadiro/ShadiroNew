from __future__ import annotations

from enum import Enum


class VehicleType(str, Enum):
    BIKE = "bike"
    CAR = "car"
    TEMPO = "tempo"
    MINI_TRUCK = "mini_truck"
    HEAVY = "heavy"


class PartnerStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class VerificationDocType(str, Enum):
    AADHAAR = "aadhaar"
    PAN = "pan"
    DRIVING_LICENSE = "driving_license"
    VEHICLE_RC = "vehicle_rc"
    SELFIE = "selfie"
    BANK_ACCOUNT = "bank_account"


class DeliveryJobState(str, Enum):
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    ARRIVING_VENDOR = "arriving_vendor"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    ARRIVING_CUSTOMER = "arriving_customer"
    DELIVERED = "delivered"
    FAILED = "failed"


class LogisticsTier(str, Enum):
    """Maps order requirements to partner vehicle classes."""

    BIKE = "bike"
    CAR = "car"
    TEMPO = "tempo"
    MINI_TRUCK = "mini_truck"
    HEAVY = "heavy"


# Minimum vehicle tier order for compatibility (index in list = rank).
TIER_ORDER: tuple[LogisticsTier, ...] = (
    LogisticsTier.BIKE,
    LogisticsTier.CAR,
    LogisticsTier.TEMPO,
    LogisticsTier.MINI_TRUCK,
    LogisticsTier.HEAVY,
)


def tier_rank(tier: str | LogisticsTier) -> int:
    raw = tier.value if isinstance(tier, LogisticsTier) else str(tier).strip().lower()
    for i, t in enumerate(TIER_ORDER):
        if t.value == raw:
            return i
    return 0


def partner_can_carry_tier(partner_max_tier: str, required: str) -> bool:
    return tier_rank(partner_max_tier) >= tier_rank(required)


COLLECTION_PARTNERS = "delivery_partners"
COLLECTION_JOBS = "delivery_jobs"
COLLECTION_QR_SESSIONS = "delivery_qr_sessions"
COLLECTION_FRAUD = "delivery_fraud_events"
COLLECTION_TRACKING = "delivery_tracking_points"
