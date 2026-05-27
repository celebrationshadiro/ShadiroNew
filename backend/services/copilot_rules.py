from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


CATEGORY_UPSELLS = {
    "venue": ["Decor & floral package", "Catering coordination", "Valet parking"],
    "grocery": ["Bulk staples bundle", "Express delivery slot", "Premium produce upgrade"],
    "dj": ["Lighting rig", "Wireless mic add-on", "After-party hour"],
    "caterer": ["Live counters", "Dessert bar", "Premium cutlery"],
    "decorator": ["Stage upgrade", "Entrance arch", "Photo backdrop"],
    "photographer": ["Drone coverage", "Same-day highlight reel", "Photo album upgrade"],
    "makeup": ["Trial session", "Touch-up kit", "Bridal party package"],
    "transport": ["Decorated vehicle", "Extra pickup run", "Premium fleet upgrade"],
    "mehandi": ["Bridal premium design", "Family package", "Color guarantee add-on"],
}


def normalize_tone(tone: Optional[str]) -> str:
    if not tone:
        return "formal"
    tone_value = tone.lower().strip()
    if tone_value in {"formal", "quick", "concise"}:
        return tone_value
    return "formal"


def _format_event_context(event: Dict[str, Any]) -> str:
    if not event:
        return "your upcoming event"
    date = event.get("date")
    location = event.get("location")
    title = event.get("title") or event.get("event_type")
    parts = []
    if title:
        parts.append(str(title))
    if date:
        parts.append(f"on {date}")
    if location:
        parts.append(f"in {location}")
    return " ".join(parts) if parts else "your upcoming event"


def _estimate_price(vendor: Dict[str, Any], service_count: int) -> Optional[float]:
    if not vendor:
        return None
    base = vendor.get("base_price")
    if base is None:
        return None
    multiplier = max(service_count, 1)
    return round(float(base) * multiplier, 2)


def build_quote_draft(
    payload: Dict[str, Any],
    vendor: Optional[Dict[str, Any]] = None,
    event: Optional[Dict[str, Any]] = None,
    quote: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    tone = normalize_tone(payload.get("tone"))
    requested_services = payload.get("requested_services") or (quote or {}).get("requested_services") or []
    category_id = payload.get("category_id") or (vendor or {}).get("category_id") or "general"
    event_context = _format_event_context(event or {})
    vendor_name = (vendor or {}).get("business_name") or "our team"
    service_list = ", ".join(requested_services) if requested_services else "your requirements"

    if tone == "quick":
        greeting = "Thanks for reaching out."
    elif tone == "concise":
        greeting = "Appreciate the inquiry."
    else:
        greeting = "Thank you for considering us."

    body = (
        f"We can support {event_context} and cover {service_list}. "
        "Please share any must-haves, timing preferences, and budget range so we can finalize the best package."
    )

    closing = "Happy to tailor the proposal further once we confirm the details." if tone != "quick" else "Share details and we will finalize."

    draft = f"{greeting} {body} {closing}"

    suggested_price = _estimate_price(vendor or {}, len(requested_services))
    upsells = CATEGORY_UPSELLS.get(str(category_id), [])

    reasoning = (
        f"Draft highlights coverage for {event_context} and acknowledges {service_list}. "
        "Suggesting clarifying questions to speed conversion."
    )

    return {
        "draft": draft,
        "reasoning": reasoning,
        "upsells": upsells,
        "suggested_price": suggested_price,
        "tone": tone,
        "vendor_name": vendor_name,
    }


def summarize_messages(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not messages:
        return {
            "summary": "No conversation yet.",
            "key_points": [],
            "next_steps": ["Send initial requirements or availability."],
        }

    last_message = messages[-1]
    summary = f"Conversation has {len(messages)} messages. Latest: {last_message.get('message', '')}".strip()

    key_points = []
    for msg in messages[-10:]:
        text = (msg.get("message") or "").lower()
        if "budget" in text:
            key_points.append("Budget discussed")
        if "date" in text or "schedule" in text:
            key_points.append("Date/timing discussed")
        if "location" in text or "venue" in text:
            key_points.append("Location discussed")
    key_points = list(dict.fromkeys(key_points))

    next_steps = ["Confirm availability", "Share final quote options"]
    return {"summary": summary, "key_points": key_points, "next_steps": next_steps}


def suggest_replies(messages: List[Dict[str, Any]], tone: Optional[str] = None) -> Dict[str, Any]:
    tone_value = normalize_tone(tone)
    last_message = messages[-1].get("message") if messages else None
    base = "Thanks for the update. We can confirm once we have the final details." if tone_value == "formal" else "Got it. Share the final details and we will lock it."
    if tone_value == "quick":
        base = "Got it. Send details and we will confirm."
    elif tone_value == "concise":
        base = "Understood. Please confirm details to proceed."

    if last_message:
        base = f"{base} (Re: '{last_message[:80]}')"

    return {
        "suggestions": [base],
        "tone": tone_value,
    }
