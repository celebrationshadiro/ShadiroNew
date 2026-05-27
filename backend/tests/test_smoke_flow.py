import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models import VendorRegistration, VendorOnboardingUpdate, QuoteCreate, OrderCreate, ReviewCreate


def test_smoke_vendor_onboarding_payloads():
    vendor = VendorRegistration(
        business_name="Test Venue",
        owner_name="Owner",
        email="owner@example.com",
        phone="1234567890",
        password="password",
        category_id="cat-venues",
        city="Mumbai",
        capacity_min=100,
        capacity_max=300,
        venue_types=["banquet"],
        amenities=["parking"],
        pricing_model="per_day",
        availability_calendar="2026-05",
        cancellation_policy="48 hours",
    )
    assert vendor.business_name == "Test Venue"

    update = VendorOnboardingUpdate(
        business_name="Test Venue",
        capacity_min=100,
        capacity_max=300,
        pricing_model="per_day",
        venue_types=["banquet"],
        amenities=["parking"],
    )
    assert update.capacity_min == 100


def test_smoke_quote_order_review_flow():
    quote = QuoteCreate(
        event_id="event_1",
        vendor_id="vendor_1",
        user_id="user_1",
        requested_services=["Photography"],
        message="Need coverage",
        attachments=[{"url": "https://example.com/ref.pdf", "filename": "ref.pdf"}],
    )
    assert quote.attachments

    order = OrderCreate(
        user_id="user_1",
        event_id="event_1",
        vendor_id="vendor_1",
        total_amount=10000,
        services=["Photography"],
    )
    assert order.total_amount == 10000

    review = ReviewCreate(
        user_id="user_1",
        vendor_id="vendor_1",
        order_id="order_1",
        rating=5,
        comment="Great service",
    )
    assert review.rating == 5
