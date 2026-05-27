from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Optional
from uuid import uuid4

from canonical_models.common import BookingIntentStatus, utcnow


@dataclass
class ParsedIntent:
    category_type: str
    category_slug: str
    confidence: float
    hints: dict[str, Any]


class AIBookingService:
    """
    Rules-first AI booking helper that can later be swapped with an LLM parser.
    Responsibilities:
    - parse user intent
    - generate booking suggestions
    - route to service category
    - create booking intent
    """

    CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
        "photography": ("photo", "photographer", "pre-wedding", "shoot"),
        "catering": ("catering", "food", "menu", "buffet"),
        "decoration": ("decor", "stage", "theme", "flowers"),
        "makeup": ("makeup", "artist", "bridal"),
        "venue": ("venue", "hall", "banquet", "lawn"),
        "music": ("dj", "music", "band", "sangeet"),
    }

    def __init__(self, db):
        self.db = db

    def parse_user_intent(self, text: str) -> ParsedIntent:
        normalized = str(text or "").strip().lower()
        if not normalized:
            return ParsedIntent(
                category_type="service",
                category_slug="general",
                confidence=0.2,
                hints={},
            )

        best_slug = "general"
        best_score = 0
        for slug, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in normalized)
            if score > best_score:
                best_slug = slug
                best_score = score

        people_match = re.search(r"(\d+)\s*(guest|people|pax)", normalized)
        budget_match = re.search(r"(?:inr|rs\.?|₹)\s*([0-9,]+)", normalized)
        hints: dict[str, Any] = {}
        if people_match:
            hints["guest_count"] = int(people_match.group(1))
        if budget_match:
            hints["budget_hint_inr"] = int(budget_match.group(1).replace(",", ""))

        confidence = 0.95 if best_score >= 2 else (0.65 if best_score == 1 else 0.3)
        return ParsedIntent(
            category_type="service",
            category_slug=best_slug,
            confidence=confidence,
            hints=hints,
        )

    async def generate_booking_suggestions(
        self,
        *,
        category_slug: str,
        city: Optional[str] = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"is_active": {"$ne": False}}
        if category_slug and category_slug != "general":
            query["category_id"] = {"$regex": category_slug, "$options": "i"}
        if city:
            query["city"] = {"$regex": f"^{re.escape(city)}$", "$options": "i"}
        docs = await self.db.vendors.find(
            query,
            {"_id": 0, "id": 1, "business_name": 1, "rating": 1, "base_price": 1, "city": 1, "category_id": 1},
        ).sort("rating", -1).limit(limit).to_list(length=limit)
        return docs

    async def route_service_category(self, user_text: str) -> dict[str, Any]:
        parsed = self.parse_user_intent(user_text)
        suggestions = await self.generate_booking_suggestions(category_slug=parsed.category_slug)
        return {
            "category_type": parsed.category_type,
            "category_slug": parsed.category_slug,
            "confidence": parsed.confidence,
            "hints": parsed.hints,
            "suggestions": suggestions,
        }

    async def create_booking_intent(
        self,
        *,
        user_id: str,
        vendor_id: str,
        items: list[dict[str, Any]],
        total_amount_paise: int,
        category_type: str = "service",
        notes: Optional[str] = None,
        meta: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        now = utcnow()
        intent_doc = {
            "id": f"bint_{uuid4().hex}",
            "idempotency_key": f"ai:{user_id}:{uuid4().hex}",
            "user_id": user_id,
            "vendor_id": vendor_id,
            "category_type": category_type,
            "items": items,
            "total_amount_paise": int(total_amount_paise),
            "scheduled_at": None,
            "duration_minutes": None,
            "notes": notes,
            "meta": {"source": "ai_assistant", **(meta or {})},
            "status": BookingIntentStatus.PENDING.value,
            "expires_at": now + timedelta(minutes=30),
            "created_at": now,
            "updated_at": now,
            "version": 1,
        }
        await self.db.booking_intents.insert_one(intent_doc)
        return intent_doc
