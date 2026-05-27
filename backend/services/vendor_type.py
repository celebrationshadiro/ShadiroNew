from __future__ import annotations

import logging
from typing import Optional

from models import VendorType

logger = logging.getLogger(__name__)

PRODUCT_CATEGORY_IDS = {"cat-grocery", "grocery"}
PRODUCT_VALUES = {"product_vendor", "product", "grocery"}
SERVICE_VALUES = {"service_vendor", "service"}


def resolve_vendor_type(category_id: Optional[str] = None, explicit: Optional[str] = None) -> VendorType:
    explicit_value = str(explicit).lower().strip() if explicit is not None else ""

    if category_id in PRODUCT_CATEGORY_IDS:
        if explicit_value and explicit_value not in PRODUCT_VALUES:
            logger.warning(
                "Vendor type mismatch for grocery category_id=%s explicit=%s; using PRODUCT_VENDOR",
                category_id,
                explicit,
            )
        return VendorType.PRODUCT_VENDOR

    if category_id:
        if explicit_value in PRODUCT_VALUES:
            logger.warning(
                "Vendor type mismatch for service category_id=%s explicit=%s; using SERVICE_VENDOR",
                category_id,
                explicit,
            )
        return VendorType.SERVICE_VENDOR

    if explicit_value in PRODUCT_VALUES:
        return VendorType.PRODUCT_VENDOR
    if explicit_value in SERVICE_VALUES:
        return VendorType.SERVICE_VENDOR

    logger.warning("Vendor type could not be resolved; defaulting to SERVICE_VENDOR")
    return VendorType.SERVICE_VENDOR


def ensure_vendor_type(vendor_doc: dict) -> VendorType:
    existing = vendor_doc.get("vendor_type") if vendor_doc else None
    resolved = resolve_vendor_type(vendor_doc.get("category_id") if vendor_doc else None, existing)
    vendor_doc["vendor_type"] = resolved.value
    return resolved
