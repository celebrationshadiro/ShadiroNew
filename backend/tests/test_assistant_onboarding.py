import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.vendor_onboarding import validate_onboarding
from services.assistant_service import generate_assistant_response


def test_validate_onboarding_grocery_missing_catalog():
    payload = {
        "category_id": "grocery",
        "business_name": "Fresh Mart",
        "owner_name": "Asha",
        "city": "Mumbai",
        "delivery_radius": "5km",
        "delivery_schedule": "9am-6pm",
    }
    result = validate_onboarding(payload)
    assert result["status"] == "incomplete"
    assert "product_catalog" in result["missing_required"]


@pytest.mark.anyio
async def test_assistant_vendor_guidance_missing_fields():
    payload = {
        "role": "vendor",
        "message": "Help me complete onboarding",
        "category_id": "grocery",
        "profile": {
            "business_name": "Fresh Mart",
            "owner_name": "Asha",
            "city": "Mumbai",
            "delivery_radius": "5km",
            "delivery_schedule": "9am-6pm",
        },
    }
    response = await generate_assistant_response(payload)
    assert response.provider == "rules"
    assert "complete onboarding" in response.reply.lower() or "add" in response.reply.lower()
    assert response.suggestions
