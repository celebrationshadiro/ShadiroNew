import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.category_vendor_profile import (
    CategoryVendorProfileValidationError,
    validate_and_normalize_vendor_details,
)


def test_vendor_details_valid_for_caterer():
    normalized = validate_and_normalize_vendor_details(
        "caterer",
        {
            "cuisine_specializations": ["Bihari", "North Indian"],
            "service_style": ["buffet"],
            "minimum_order_quantity": 50,
        },
    )
    assert normalized["minimum_order_quantity"] == 50
    assert "cuisine_specializations" in normalized


def test_vendor_details_invalid_type():
    with pytest.raises(CategoryVendorProfileValidationError):
        validate_and_normalize_vendor_details(
            "venue",
            {
                "capacity_min": "large",
                "capacity_max": 500,
            },
        )


def test_vendor_details_forbid_unknown_field():
    with pytest.raises(CategoryVendorProfileValidationError):
        validate_and_normalize_vendor_details(
            "dj",
            {
                "genres": ["Bollywood"],
                "unexpected_key": "not_allowed",
            },
        )
