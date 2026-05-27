import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.copilot_rules import build_quote_draft, summarize_messages, suggest_replies


def test_build_quote_draft_basic():
    payload = {
        "tone": "formal",
        "requested_services": ["DJ", "Lighting"],
        "category_id": "dj",
    }
    vendor = {"business_name": "Pulse Audio", "base_price": 10000}
    event = {"title": "Wedding", "date": "2026-06-12", "location": "Delhi"}

    result = build_quote_draft(payload, vendor=vendor, event=event, quote=None)
    assert "draft" in result
    assert "reasoning" in result
    assert result["upsells"]
    assert result["suggested_price"] == 20000


def test_summarize_messages_empty():
    summary = summarize_messages([])
    assert summary["summary"] == "No conversation yet."


def test_suggest_replies_tone():
    messages = [{"message": "Can we do 8 PM?"}]
    suggestion = suggest_replies(messages, tone="quick")
    assert suggestion["tone"] == "quick"
    assert suggestion["suggestions"]
