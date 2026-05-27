import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.category_booking_flow import (
    CategoryBookingValidationError,
    build_payment_plan,
    get_booking_flow_template,
    normalize_category_id,
    validate_and_normalize_booking_details,
    validate_booking_details,
)


def test_normalize_category_id_alias():
    assert normalize_category_id("planner") == "event_planner"
    assert normalize_category_id("catering") == "caterer"


def test_validate_booking_details_for_caterer():
    missing = validate_booking_details(
        "caterer",
        {
            "event_date": "2026-03-10",
            "event_city": "Patna",
            "event_location": "Boring Road",
        },
    )
    assert "guest_count" in missing
    assert "service_style" in missing


def test_build_payment_plan_uses_category_advance():
    plan = build_payment_plan(10000, "venue")
    assert plan["advance_percentage"] == 20
    assert plan["advance_amount"] == 2000
    assert plan["remaining_amount"] == 8000


def test_get_booking_flow_template_has_inputs():
    template = get_booking_flow_template("dj")
    assert template is not None
    assert template["category_id"] == "dj"
    assert len(template["booking_inputs"]) > 0


def test_validate_and_normalize_booking_details_valid():
    normalized = validate_and_normalize_booking_details(
        "caterer",
        {
            "event_date": "2026-03-10",
            "event_city": "Patna",
            "event_location": "Boring Road",
            "guest_count": 120,
            "service_style": "buffet",
        },
    )
    assert normalized["event_date"] == "2026-03-10"
    assert normalized["guest_count"] == 120


def test_validate_and_normalize_booking_details_invalid_enum():
    with pytest.raises(CategoryBookingValidationError):
        validate_and_normalize_booking_details(
            "dj",
            {
                "event_date": "2026-03-10",
                "start_time": "18:00:00",
                "end_time": "22:00:00",
                "event_city": "Patna",
                "event_location": "Kankarbagh",
                "music_preference": "classical_only",
            },
        )


def test_validate_and_normalize_booking_details_forbids_extra_keys():
    with pytest.raises(CategoryBookingValidationError):
        validate_and_normalize_booking_details(
            "venue",
            {
                "event_date": "2026-03-10",
                "event_city": "Patna",
                "guest_count": 300,
                "slot": "evening",
                "random_field": "not_allowed",
            },
        )
