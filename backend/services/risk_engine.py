from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime, timezone


def compute_cancellation_risk(vendor: Dict[str, Any], booking: Dict[str, Any]) -> Dict[str, Any]:
    score = 50
    reasons = []

    acceptance_rate = float(vendor.get("acceptance_rate", 0) or 0)
    if acceptance_rate < 0.4:
        score += 20
        reasons.append("Low acceptance rate")
    elif acceptance_rate < 0.7:
        score += 10
        reasons.append("Moderate acceptance rate")

    emergency_count = int(vendor.get("emergency_count", 0) or 0)
    if emergency_count >= 3:
        score += 15
        reasons.append("Multiple emergency cancellations")
    elif emergency_count > 0:
        score += 5
        reasons.append("Past emergency cancellation")

    # Lead time
    event_date = booking.get("event_date")
    if event_date:
        try:
            event_dt = datetime.fromisoformat(event_date)
            days_until = (event_dt - datetime.now(timezone.utc)).days
            if days_until <= 7:
                score += 10
                reasons.append("Event is within 7 days")
        except Exception:
            pass

    score = max(0, min(100, score))
    if score >= 70:
        label = "High"
    elif score >= 40:
        label = "Medium"
    else:
        label = "Low"

    return {"score": score, "label": label, "reasons": reasons}


def recommend_refund_action(risk: Dict[str, Any], booking: Dict[str, Any]) -> Dict[str, Any]:
    if booking.get("status") in {"cancelled_by_vendor", "cancelled_by_vendor_emergency"}:
        if risk.get("label") == "High":
            return {"action": "full_refund", "reason": "High cancellation risk + vendor cancelled"}
        return {"action": "partial_refund", "reason": "Vendor cancelled"}
    return {"action": "no_action", "reason": "Booking active"}
