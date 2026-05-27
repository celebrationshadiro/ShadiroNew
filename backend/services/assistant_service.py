from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import os
import logging

from services.vendor_onboarding import validate_onboarding, get_requirements

logger = logging.getLogger(__name__)


@dataclass
class AssistantResponse:
    reply: str
    suggestions: List[str]
    actions: List[Dict[str, Any]]
    provider: str
    confidence: float
    metadata: Dict[str, Any]


class BaseAssistantProvider:
    name = "base"

    async def generate(self, payload: Dict[str, Any]) -> AssistantResponse:
        raise NotImplementedError


class RulesAssistantProvider(BaseAssistantProvider):
    name = "rules"

    async def generate(self, payload: Dict[str, Any]) -> AssistantResponse:
        message = (payload.get("message") or "").lower()
        role = (payload.get("role") or "user").lower()
        language = (payload.get("language") or "en").lower()
        category_id = payload.get("category_id")
        vendor_type = payload.get("vendor_type")
        profile = payload.get("profile") or {}
        event = payload.get("event") or {}

        onboarding = validate_onboarding({**profile, "category_id": category_id}) if category_id else None

        is_onboarding = any(
            key in message
            for key in ["register", "onboard", "profile", "missing", "required", "approval"]
        ) or role == "vendor"

        if language in ("hi", "hinglish"):
            return self._build_hinglish_response(role, message, onboarding, event, category_id, vendor_type)

        return self._build_english_response(role, message, onboarding, event, category_id, vendor_type)

    def _build_english_response(
        self,
        role: str,
        message: str,
        onboarding: Optional[Dict[str, Any]],
        event: Dict[str, Any],
        category_id: Optional[str],
        vendor_type: Optional[str],
    ) -> AssistantResponse:
        suggestions: List[str] = []
        actions: List[Dict[str, Any]] = []
        confidence = 0.72
        metadata: Dict[str, Any] = {}

        if role == "vendor" and (vendor_type or "").lower() in {"product_vendor", "product", "grocery"}:
            reply = (
                "You are set up as a grocery vendor. I can help you add products, set prices, and manage stock levels."
            )
            suggestions = [
                "Add new grocery items",
                "Update stock levels",
                "Set delivery slots",
            ]
            actions = [
                {"type": "open_grocery_inventory"},
                {"type": "open_grocery_orders"},
            ]
            confidence = 0.84
            return AssistantResponse(
                reply=reply,
                suggestions=suggestions,
                actions=actions,
                provider=self.name,
                confidence=confidence,
                metadata=metadata,
            )

        if role == "vendor" and (vendor_type or "").lower() in {"product_vendor", "product", "grocery"}:
            reply = (
                "Aap grocery vendor hain. Main aapki product listing, pricing, aur stock manage karne mein madad kar sakta/sakti hoon."
            )
            suggestions = [
                "Naye items add karein",
                "Stock update karein",
                "Delivery slots set karein",
            ]
            actions = [
                {"type": "open_grocery_inventory"},
                {"type": "open_grocery_orders"},
            ]
            confidence = 0.84
            return AssistantResponse(
                reply=reply,
                suggestions=suggestions,
                actions=actions,
                provider=self.name,
                confidence=confidence,
                metadata=metadata,
            )

        if role == "vendor" and onboarding:
            missing = onboarding.get("missing_required", [])
            missing_rec = onboarding.get("missing_recommended", [])
            label = onboarding.get("label", "your category")
            if missing:
                reply = (
                    f"To complete onboarding for {label}, please add: {', '.join(missing)}. "
                    "I can guide you through each field or help organize your catalog/services."
                )
                suggestions = [
                    "Show required fields checklist",
                    "Help me prepare my catalog/portfolio",
                    "Update my availability",
                ]
                actions = [
                    {"type": "open_onboarding", "category": category_id},
                    {"type": "show_missing_fields", "fields": missing},
                ]
                confidence = 0.82
            else:
                reply = (
                    f"Your onboarding for {label} looks complete. Would you like to refine pricing, "
                    "add media, or set your availability calendar?"
                )
                suggestions = ["Optimize pricing", "Add portfolio/media", "Set availability"]
                actions = [{"type": "open_vendor_dashboard"}]
            metadata["onboarding"] = onboarding
        else:
            if (category_id or "") == "grocery":
                reply = (
                    "Browse grocery vendors, add items to your cart, and checkout with a delivery address. "
                    "I can help you find essentials and track delivery."
                )
                suggestions = [
                    "Find grocery vendors near me",
                    "Create a essentials cart",
                    "Track my grocery order",
                ]
                actions = [{"type": "open_grocery_browse"}]
                confidence = 0.8
            else:
                reply = (
                    "Tell me about your event needs (date, city, budget, category), and I will shortlist "
                    "vendors and help you request quotes."
                )
                suggestions = [
                    "Find vendors under a budget",
                    "Compare venues",
                    "Build a multi-vendor plan",
                ]
                actions = [{"type": "open_vendor_search"}]

        if event:
            metadata["event_summary"] = event

        return AssistantResponse(
            reply=reply,
            suggestions=suggestions,
            actions=actions,
            provider=self.name,
            confidence=confidence,
            metadata=metadata,
        )

    def _build_hinglish_response(
        self,
        role: str,
        message: str,
        onboarding: Optional[Dict[str, Any]],
        event: Dict[str, Any],
        category_id: Optional[str],
        vendor_type: Optional[str],
    ) -> AssistantResponse:
        suggestions: List[str] = []
        actions: List[Dict[str, Any]] = []
        confidence = 0.72
        metadata: Dict[str, Any] = {}

        if role == "vendor" and onboarding:
            missing = onboarding.get("missing_required", [])
            label = onboarding.get("label", "aapki category")
            if missing:
                reply = (
                    f"{label} onboarding complete karne ke liye yeh fields add karein: {', '.join(missing)}. "
                    "Main step-by-step help kar sakta/ sakti hoon."
                )
                suggestions = [
                    "Required fields checklist",
                    "Catalog/portfolio banane mein help",
                    "Availability update",
                ]
                actions = [
                    {"type": "open_onboarding", "category": category_id},
                    {"type": "show_missing_fields", "fields": missing},
                ]
                confidence = 0.82
            else:
                reply = (
                    f"{label} onboarding complete hai. Kya aap pricing optimize ya portfolio add karna chahenge?"
                )
                suggestions = ["Pricing optimize", "Portfolio add", "Availability set"]
                actions = [{"type": "open_vendor_dashboard"}]
            metadata["onboarding"] = onboarding
        else:
            if (category_id or "") == "grocery":
                reply = (
                    "Grocery vendors browse karein, items cart mein add karein, aur delivery address ke saath checkout karein."
                )
                suggestions = [
                    "Grocery vendors dhoondein",
                    "Essentials cart banayein",
                    "Order track karein",
                ]
                actions = [{"type": "open_grocery_browse"}]
                confidence = 0.8
            else:
                reply = (
                    "Apne event details share karein (date, city, budget, category). Main best vendors shortlist kar dunga/dungi."
                )
                suggestions = [
                    "Budget ke andar vendors",
                    "Venues compare",
                    "Multi-vendor plan",
                ]
                actions = [{"type": "open_vendor_search"}]
            suggestions = [
                "Budget ke andar vendors",
                "Venues compare",
                "Multi-vendor plan",
            ]
            actions = [{"type": "open_vendor_search"}]

        if event:
            metadata["event_summary"] = event

        return AssistantResponse(
            reply=reply,
            suggestions=suggestions,
            actions=actions,
            provider=self.name,
            confidence=confidence,
            metadata=metadata,
        )


class LLMPlaceholderProvider(BaseAssistantProvider):
    def __init__(self, provider_name: str):
        self.name = f"{provider_name}-placeholder"
        self.provider_name = provider_name

    async def generate(self, payload: Dict[str, Any]) -> AssistantResponse:
        return AssistantResponse(
            reply="LLM provider is not configured yet. Falling back to rules-based guidance.",
            suggestions=["Use rules-based assistant"],
            actions=[],
            provider=self.name,
            confidence=0.2,
            metadata={"fallback": "rules", "requested_provider": self.provider_name},
        )


def get_provider() -> BaseAssistantProvider:
    provider = os.environ.get("ASSISTANT_PROVIDER", "rules").lower()
    if provider == "rules":
        return RulesAssistantProvider()
    logger.warning("ASSISTANT_PROVIDER not configured for %s. Using placeholder.", provider)
    return LLMPlaceholderProvider(provider)


async def generate_assistant_response(payload: Dict[str, Any]) -> AssistantResponse:
    provider = get_provider()
    response = await provider.generate(payload)
    if response.provider != "rules" and response.metadata.get("fallback") == "rules":
        fallback = RulesAssistantProvider()
        return await fallback.generate(payload)
    return response
