from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

WEEKEND_DAYS = {"sat", "sun"}


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _weekday_label(dt: datetime) -> str:
    return dt.strftime("%a").lower()[:3]


def apply_pricing_rules(
    base_amount: float,
    event_date: Optional[str],
    rules: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Apply vendor pricing rules to a base amount for preview."""
    base_amount = float(base_amount or 0)
    applied_rules: List[Dict[str, Any]] = []
    total_multiplier = 1.0
    total_flat = 0.0

    event_dt = _parse_date(event_date)
    weekday = _weekday_label(event_dt) if event_dt else None

    for rule in rules or []:
        start = _parse_date(rule.get("start_date"))
        end = _parse_date(rule.get("end_date"))
        days = [d.lower()[:3] for d in (rule.get("days_of_week") or [])]
        multiplier = float(rule.get("multiplier")) if rule.get("multiplier") is not None else 1.0
        flat_fee = float(rule.get("flat_fee")) if rule.get("flat_fee") is not None else 0.0

        if event_dt:
            if start and event_dt < start:
                continue
            if end and event_dt > end:
                continue
        if days and weekday and weekday not in days:
            continue

        if multiplier != 1.0:
            total_multiplier *= multiplier
        if flat_fee:
            total_flat += flat_fee
        applied_rules.append({
            "id": rule.get("id"),
            "label": rule.get("label"),
            "multiplier": multiplier,
            "flat_fee": flat_fee,
        })

    total = round(base_amount * total_multiplier + total_flat, 2)
    return {
        "base_amount": base_amount,
        "multiplier": round(total_multiplier, 2),
        "flat_fee": round(total_flat, 2),
        "total": total,
        "applied_rules": applied_rules,
    }
