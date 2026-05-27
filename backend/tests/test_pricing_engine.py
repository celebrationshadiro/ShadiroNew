import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.pricing_engine import apply_pricing_rules


def test_pricing_rules_apply_multiplier_and_flat_fee():
    rules = [
        {
            "id": "rule1",
            "label": "Weekend",
            "days_of_week": ["sat", "sun"],
            "multiplier": 1.2,
            "flat_fee": 500,
        }
    ]
    result = apply_pricing_rules(10000, "2026-02-14", rules)
    assert result["multiplier"] == 1.2
    assert result["flat_fee"] == 500
    assert result["total"] == 12500


def test_pricing_rules_skip_non_matching_day():
    rules = [
        {
            "id": "rule2",
            "label": "Weekend",
            "days_of_week": ["sat", "sun"],
            "multiplier": 1.3,
        }
    ]
    result = apply_pricing_rules(8000, "2026-02-11", rules)
    assert result["multiplier"] == 1.0
    assert result["total"] == 8000
