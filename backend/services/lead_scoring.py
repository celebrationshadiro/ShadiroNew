from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, Optional


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _days_until(date_value: Optional[str]) -> Optional[int]:
    dt = _parse_date(date_value)
    if not dt:
        return None
    now = datetime.utcnow()
    return (dt - now).days


def compute_lead_score(
    event: Dict[str, Any],
    vendor: Dict[str, Any],
    user_history_count: int = 0,
) -> Dict[str, Any]:
    score = 50
    reasons = []

    days_until = _days_until(event.get("date"))
    if days_until is not None:
        if days_until <= 7:
            score += 30
            reasons.append("Event within 7 days")
        elif days_until <= 30:
            score += 20
            reasons.append("Event within 30 days")
        elif days_until <= 90:
            score += 10
            reasons.append("Event within 90 days")

    budget_max = event.get("budget_max") or event.get("budget")
    vendor_base = vendor.get("base_price")
    if budget_max and vendor_base:
        if float(budget_max) >= float(vendor_base):
            score += 15
            reasons.append("Budget aligns with base price")
        else:
            score -= 10
            reasons.append("Budget below base price")

    if user_history_count >= 3:
        score += 10
        reasons.append("Repeat customer")
    elif user_history_count == 0:
        score -= 5
        reasons.append("New customer")

    if vendor.get("is_available") is False:
        score -= 20
        reasons.append("Vendor marked unavailable")

    next_available = _parse_date(vendor.get("next_available_date"))
    event_date = _parse_date(event.get("date"))
    if next_available and event_date and next_available > event_date:
        score -= 15
        reasons.append("Vendor available after event date")

    score = max(0, min(100, score))
    if score >= 70:
        label = "Hot"
    elif score >= 40:
        label = "Warm"
    else:
        label = "Cold"

    return {
        "score": score,
        "label": label,
        "reasons": reasons,
    }
