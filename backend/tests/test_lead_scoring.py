import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.lead_scoring import compute_lead_score


def test_lead_score_hot_for_urgent_event():
    event = {"date": "2026-02-12", "budget_max": 50000}
    vendor = {"base_price": 20000, "is_available": True}
    result = compute_lead_score(event, vendor, user_history_count=2)
    assert result["label"] in {"Hot", "Warm"}
    assert result["score"] >= 60


def test_lead_score_cold_for_unavailable_vendor():
    event = {"date": "2027-12-31", "budget_max": 10000}
    vendor = {"base_price": 25000, "is_available": False}
    result = compute_lead_score(event, vendor, user_history_count=0)
    assert result["label"] == "Cold"
