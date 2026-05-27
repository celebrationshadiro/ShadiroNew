import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.lead_scoring import compute_lead_score
from services.pricing_engine import apply_pricing_rules
from services.automation_engine import normalize_schedule


def test_normalize_schedule_valid():
    run_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    payload = {
        "type": "quote_followup",
        "run_at": run_at,
        "payload": {"message": "Reminder"},
    }
    result = normalize_schedule(payload)
    assert result["type"] == "quote_followup"
    assert result["status"] == "pending"


def test_normalize_schedule_invalid_type():
    run_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    payload = {
        "type": "unknown",
        "run_at": run_at,
    }
    try:
        normalize_schedule(payload)
        assert False, "Expected ValueError"
    except ValueError:
        assert True
