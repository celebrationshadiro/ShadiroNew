import os
from typing import Any, Dict, Tuple

from models import VendorType


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return float(default)
    try:
        return float(raw)
    except (TypeError, ValueError):
        return float(default)


def get_default_commission_config() -> Dict[str, Dict[str, float]]:
    return {
        VendorType.SERVICE_VENDOR.value: {
            "percentage": _env_float("SERVICE_COMMISSION_PERCENT", 5.0),
            "minimum": _env_float("SERVICE_MIN_COMMISSION", 1000.0),
        },
        VendorType.PRODUCT_VENDOR.value: {
            "percentage": _env_float("WHOLESALE_COMMISSION_PERCENT", 3.0),
            "minimum": _env_float("WHOLESALE_MIN_COMMISSION", 300.0),
        },
    }


def _normalize_vendor_type(vendor_doc: Dict[str, Any]) -> str:
    vt = vendor_doc.get("vendor_type") or VendorType.SERVICE_VENDOR.value
    if isinstance(vt, VendorType):
        return vt.value
    return str(vt)


def get_commission_profile(vendor_doc: Dict[str, Any]) -> Dict[str, float]:
    defaults = get_default_commission_config()
    vendor_type = _normalize_vendor_type(vendor_doc)
    base = defaults.get(vendor_type, defaults[VendorType.SERVICE_VENDOR.value])

    percentage = vendor_doc.get("commission_percentage")
    minimum = vendor_doc.get("minimum_commission")

    if percentage is None:
        percentage = base["percentage"]
    if minimum is None:
        minimum = base["minimum"]

    return {
        "vendor_type": vendor_type,
        "commission_percentage": float(percentage),
        "minimum_commission": float(minimum),
    }


def compute_commission(amount: float, commission_percentage: float, minimum_commission: float) -> Tuple[float, float]:
    pct_amount = (float(amount) * float(commission_percentage)) / 100.0
    commission_amount = max(pct_amount, float(minimum_commission))
    net_amount = float(amount) - commission_amount
    return round(commission_amount, 2), round(net_amount, 2)


def compute_gateway_fee(amount: float) -> float:
    percent = _env_float("PAYMENT_GATEWAY_FEE_PERCENT", 0.0)
    fixed = _env_float("PAYMENT_GATEWAY_FEE_FIXED", 0.0)
    fee = (float(amount) * percent) / 100.0 + fixed
    return round(fee, 2)


def build_commission_breakdown(vendor_doc: Dict[str, Any], amount: float) -> Dict[str, float]:
    profile = get_commission_profile(vendor_doc)
    commission_amount, net_amount = compute_commission(
        amount, profile["commission_percentage"], profile["minimum_commission"]
    )
    gateway_fee = compute_gateway_fee(amount)
    return {
        "commission_percentage": profile["commission_percentage"],
        "minimum_commission": profile["minimum_commission"],
        "commission_amount": commission_amount,
        "net_amount": net_amount,
        "gateway_fee": gateway_fee,
    }
