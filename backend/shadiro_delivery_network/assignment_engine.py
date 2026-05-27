from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Any


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlmb = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(p1) * cos(p2) * sin(dlmb / 2) ** 2
    return 2 * r * asin(sqrt(a))


def partner_max_tier(vehicle_types: list[str]) -> str:
    from shadiro_delivery_network.constants import LogisticsTier, TIER_ORDER

    best = 0
    best_t = LogisticsTier.BIKE.value
    for vt in vehicle_types or []:
        raw = str(vt).strip().lower()
        for i, t in enumerate(TIER_ORDER):
            if t.value == raw and i >= best:
                best = i
                best_t = t.value
    return best_t


def score_partner(
    partner: dict[str, Any],
    *,
    pickup_lat: float,
    pickup_lng: float,
    traffic_factor: float = 1.0,
) -> float:
    """
    Higher is better. Considers distance, rating, acceptance, workload, fraud, vehicle match implicit upstream.
    """
    plat = partner.get("last_lat")
    plng = partner.get("last_lng")
    if plat is None or plng is None:
        distance_km = 50.0
    else:
        distance_km = max(0.05, haversine_km(float(plat), float(plng), pickup_lat, pickup_lng)) * traffic_factor

    rating = float(partner.get("rating_avg") or 4.2)
    acceptance = float(partner.get("acceptance_rate") or 0.85)
    load = int(partner.get("active_job_count") or 0)
    fraud = float(partner.get("fraud_score") or 0.0)
    battery = float(partner.get("network_reliability") or 0.9)

    dist_component = 120.0 / (1.0 + distance_km)
    score = (
        dist_component * 1.4
        + rating * 8.0
        + acceptance * 25.0
        + battery * 5.0
        - load * 12.0
        - fraud * 40.0
    )
    return score


def rank_partners(
    partners: list[dict[str, Any]],
    *,
    pickup_lat: float,
    pickup_lng: float,
    limit: int = 25,
) -> list[dict[str, Any]]:
    enriched = []
    for p in partners:
        s = score_partner(p, pickup_lat=pickup_lat, pickup_lng=pickup_lng)
        enriched.append({**p, "_assignment_score": s})
    enriched.sort(key=lambda x: float(x.get("_assignment_score") or 0), reverse=True)
    return enriched[:limit]
