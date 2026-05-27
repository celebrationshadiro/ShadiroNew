"""Replacement matcher service for suggesting replacement vendors.

Simple heuristics:
- match category
- match city (case-insensitive regex)
- exclude vendor ids
- score by price proximity and rating
"""
from typing import List, Optional
from datetime import datetime, timezone


async def find_replacement_vendors(db, category_id: Optional[str], city: Optional[str], target_price: Optional[float], exclude_ids: List[str] = None, limit: int = 5):
    """Return list of candidate vendors (dicts) ordered by a simple score.

    db: motor client database
    category_id: vendor category to match
    city: city name or partial
    target_price: target amount to match price range
    exclude_ids: vendor ids to exclude
    limit: number of candidates to return
    """
    exclude_ids = exclude_ids or []
    query = {"status": "approved", "is_active": True}
    if category_id:
        query["category_id"] = category_id
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    if exclude_ids:
        query["id"] = {"$nin": exclude_ids}

    # Fetch candidates (limit a bit higher than final limit for scoring)
    candidates = await db.vendors.find(query, {"_id": 0, "id": 1, "business_name": 1, "price_min": 1, "price_max": 1, "base_price": 1, "rating": 1}).to_list(50)

    def vendor_avg_price(v):
        if v.get("price_min") and v.get("price_max"):
            return (v.get("price_min") + v.get("price_max")) / 2
        if v.get("base_price"):
            return v.get("base_price")
        return None

    scored = []
    for v in candidates:
        avg = vendor_avg_price(v)
        # price_score: lower is better; if no target or avg, treat as middle score
        if target_price is None or avg is None:
            price_score = 1.0
        else:
            price_score = abs((avg - target_price) / (target_price + 1e-6))

        rating = v.get("rating") or 0.0
        # final score: combine price_score and inverse rating
        score = price_score * 0.7 + (1.0 - min(rating / 5.0, 1.0)) * 0.3
        scored.append((score, v))

    scored.sort(key=lambda x: x[0])
    results = [v for _, v in scored[:limit]]
    return results
