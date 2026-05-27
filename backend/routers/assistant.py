"""Assistant endpoints for AI vendor assistant (rules-based, LLM-ready)."""
from fastapi import APIRouter, Depends, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, Dict, Any, List

from core.security import get_current_user, get_current_user_optional
from services.assistant_service import generate_assistant_response
from services.ai_booking_service import AIBookingService
from services.copilot_service import (
    generate_quote_draft,
    generate_negotiation_summary,
    generate_reply_suggestions,
)
from services.vendor_onboarding import validate_onboarding, get_requirements
from models import (
    QuoteDraftRequest,
    QuoteDraftResponse,
    NegotiationSummaryRequest,
    NegotiationSummaryResponse,
    ReplySuggestRequest,
    ReplySuggestResponse,
    UserRole,
    VendorType,
)
from services.vendor_type import resolve_vendor_type

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


def get_db(request: Request) -> AsyncIOMotorDatabase:
    """Dependency to get the database connection."""
    return request.app.state.db


async def get_current_vendor(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Optional[Dict[str, Any]]:
    """Returns vendor doc if current user is a vendor, otherwise None."""
    if current_user.get("role") == UserRole.VENDOR:
        return await db.vendors.find_one({"user_id": current_user["id"]}, {"_id": 0})
    return None


@router.post("/message")
async def assistant_message(payload: Dict[str, Any], db: AsyncIOMotorDatabase = Depends(get_db), current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Main assistant endpoint."""
    if not payload or not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid payload")

    # Enrich payload with user role if missing
    if current_user:
        payload["role"] = current_user.get("role", UserRole.CUSTOMER)
        payload["user_id"] = current_user.get("id")
        if current_user.get("role") == UserRole.VENDOR:
            vendor_doc = await db.vendors.find_one({"user_id": current_user.get("id")}, {"_id": 0, "vendor_type": 1, "category_id": 1})
            if vendor_doc:
                payload.setdefault("vendor_type", resolve_vendor_type(vendor_doc.get("category_id"), vendor_doc.get("vendor_type")).value)
                payload.setdefault("category_id", vendor_doc.get("category_id"))
    else:
        payload.setdefault("role", payload.get("role", "user"))

    response = await generate_assistant_response(payload)
    return {
        "reply": response.reply,
        "suggestions": response.suggestions,
        "actions": response.actions,
        "provider": response.provider,
        "confidence": response.confidence,
        "metadata": response.metadata,
    }


@router.post("/quote/draft", response_model=QuoteDraftResponse)
async def assistant_quote_draft(
    payload: QuoteDraftRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    vendor_doc = None
    quote_doc = None
    event_doc = None

    if current_user.get("role") == UserRole.VENDOR:
        vendor_doc = await db.vendors.find_one({"user_id": current_user["id"]}, {"_id": 0})
    elif current_user.get("role") == UserRole.ADMIN and payload.vendor_id:
        vendor_doc = await db.vendors.find_one({"id": payload.vendor_id}, {"_id": 0})

    if payload.quote_id:
        quote_doc = await db.quotes.find_one({"id": payload.quote_id}, {"_id": 0})
        if quote_doc and not vendor_doc:
            vendor_doc = await db.vendors.find_one({"id": quote_doc.get("vendor_id")}, {"_id": 0})
    if payload.event_id:
        event_doc = await db.events.find_one({"id": payload.event_id}, {"_id": 0})
    elif quote_doc:
        event_doc = await db.events.find_one({"id": quote_doc.get("event_id")}, {"_id": 0})

    if vendor_doc and resolve_vendor_type(vendor_doc.get("category_id"), vendor_doc.get("vendor_type")) == VendorType.PRODUCT_VENDOR:
        raise HTTPException(status_code=400, detail="Grocery vendors do not use quote drafts")

    result = await generate_quote_draft(payload.model_dump(), vendor_doc, event_doc, quote_doc)
    return QuoteDraftResponse(**result)


@router.post("/negotiation/summary", response_model=NegotiationSummaryResponse)
async def assistant_negotiation_summary(
    payload: NegotiationSummaryRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    vendor_doc: Optional[Dict[str, Any]] = Depends(get_current_vendor),
):
    messages = await _get_messages_from_chat(db, payload.chat_id, payload.messages)
    result = await generate_negotiation_summary(messages, vendor_doc)
    return NegotiationSummaryResponse(**result)


async def _get_messages_from_chat(
    db: AsyncIOMotorDatabase, chat_id: Optional[str], existing_messages: Optional[List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """Fetches chat messages from DB if not provided."""
    if existing_messages:
        return existing_messages
    if chat_id:
        cursor = db.chat_messages.find({"chat_id": chat_id}, {"_id": 0}).sort("timestamp", 1).limit(50)
        return await cursor.to_list(length=50)
    return []


@router.post("/reply/suggest", response_model=ReplySuggestResponse)
async def assistant_reply_suggest(
    payload: ReplySuggestRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    vendor_doc: Optional[Dict[str, Any]] = Depends(get_current_vendor),
):
    messages = await _get_messages_from_chat(db, payload.chat_id, payload.messages)
    tone_value = payload.tone.value if payload.tone else None
    result = await generate_reply_suggestions(messages, tone=tone_value, vendor=vendor_doc)
    return ReplySuggestResponse(**result)


@router.post("/onboarding/validate")
async def assistant_onboarding_validate(payload: Dict[str, Any], current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Validate onboarding fields for a vendor profile draft."""
    if not payload or not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid payload")
    result = validate_onboarding(payload)
    return result


@router.get("/onboarding/requirements/{category_id}")
async def assistant_onboarding_requirements(category_id: str, current_user: Optional[dict] = Depends(get_current_user_optional)):
    return get_requirements(category_id)


@router.get("/health")
async def assistant_health():
    return {"status": "ok"}


@router.post("/booking/route")
async def assistant_booking_route(
    payload: Dict[str, Any],
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    user_text = str(payload.get("message") or payload.get("query") or "")
    if not user_text:
        raise HTTPException(status_code=400, detail="message is required")
    ai_booking = AIBookingService(db)
    route = await ai_booking.route_service_category(user_text=user_text)
    route["user_id"] = str((current_user or {}).get("id") or "")
    return route
