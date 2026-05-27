import pytest
from pydantic import ValidationError

from app.api.v1.schemas.catalog import PackageCreate, ReviewCreate, VendorCreate


def test_review_rating_is_bounded():
    with pytest.raises(ValidationError):
        ReviewCreate(vendor_id="ven_1", rating=6)


def test_package_price_cannot_be_negative():
    with pytest.raises(ValidationError):
        PackageCreate(vendor_id="ven_1", name="Premium", price=-1)


def test_vendor_requires_business_name_and_category():
    vendor = VendorCreate(business_name="Shadiro Decor", category_id="decor")

    assert vendor.business_name == "Shadiro Decor"
    assert vendor.category_id == "decor"
