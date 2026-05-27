from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from services.llm_provider import get_llm_provider
from services.copilot_rules import build_quote_draft, summarize_messages, suggest_replies


def _bool_env(name: str, default: bool = True) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y"}


def is_copilot_enabled_for_vendor(vendor: Optional[Dict[str, Any]]) -> bool:
    if not _bool_env("ASSISTANT_COPILOT_ENABLED", True):
        return False
    if not vendor:
        return False
    plan = (vendor.get("subscription_plan") or "free").lower()
    allowed = os.environ.get("AI_ENABLED_PLANS", "pro,enterprise").lower().split(",")
    allowed = {p.strip() for p in allowed if p.strip()}
    return plan in allowed


def _provider_metadata(provider_name: str) -> Dict[str, Any]:
    return {
        "llm_provider": provider_name,
        "llm_ready": provider_name != "rules",
    }


async def generate_quote_draft(payload: Dict[str, Any], vendor: Optional[Dict[str, Any]], event: Optional[Dict[str, Any]], quote: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    ai_enabled = is_copilot_enabled_for_vendor(vendor)
    provider = get_llm_provider()

    if ai_enabled and provider.name != "base" and provider.is_ready():
        # LLM integration placeholder; fallback to rules for now.
        rules_output = build_quote_draft(payload, vendor, event, quote)
        return {
            **rules_output,
            "provider": provider.name,
            "ai_enabled": True,
            "confidence": 0.5,
            "metadata": {**_provider_metadata(provider.name), "fallback": "rules"},
        }

    rules_output = build_quote_draft(payload, vendor, event, quote)
    return {
        **rules_output,
        "provider": "rules",
        "ai_enabled": ai_enabled,
        "confidence": 0.78,
        "metadata": _provider_metadata("rules"),
    }


async def generate_negotiation_summary(messages: List[Dict[str, Any]], vendor: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    ai_enabled = is_copilot_enabled_for_vendor(vendor)
    provider = get_llm_provider()

    if ai_enabled and provider.name != "base" and provider.is_ready():
        rules_output = summarize_messages(messages)
        return {
            **rules_output,
            "provider": provider.name,
            "ai_enabled": True,
            "confidence": 0.5,
            "metadata": {**_provider_metadata(provider.name), "fallback": "rules"},
        }

    rules_output = summarize_messages(messages)
    return {
        **rules_output,
        "provider": "rules",
        "ai_enabled": ai_enabled,
        "confidence": 0.75,
        "metadata": _provider_metadata("rules"),
    }


async def generate_reply_suggestions(messages: List[Dict[str, Any]], tone: Optional[str] = None, vendor: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    ai_enabled = is_copilot_enabled_for_vendor(vendor)
    provider = get_llm_provider()

    if ai_enabled and provider.name != "base" and provider.is_ready():
        rules_output = suggest_replies(messages, tone=tone)
        return {
            **rules_output,
            "provider": provider.name,
            "ai_enabled": True,
            "confidence": 0.5,
            "metadata": {**_provider_metadata(provider.name), "fallback": "rules"},
        }

    rules_output = suggest_replies(messages, tone=tone)
    return {
        **rules_output,
        "provider": "rules",
        "ai_enabled": ai_enabled,
        "confidence": 0.7,
        "metadata": _provider_metadata("rules"),
    }
