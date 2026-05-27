from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any

from auth import get_current_user
from models import PricingPreviewRequest, PricingPreviewResponse
from services.pricing_engine import apply_pricing_rules

router = APIRouter(prefix="/api/pricing", tags=["pricing"])


@router.post("/preview", response_model=PricingPreviewResponse)
async def pricing_preview(
    payload: PricingPreviewRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.db
    vendor_doc = await db.vendors.find_one({"id": payload.vendor_id}, {"_id": 0})
    if not vendor_doc:
        raise HTTPException(status_code=404, detail="Vendor not found")

    base_amount = payload.base_amount
    if base_amount is None:
        base_amount = vendor_doc.get("base_price") or 0

    preview = apply_pricing_rules(base_amount, payload.event_date, vendor_doc.get("pricing_rules") or [])
    return PricingPreviewResponse(vendor_id=payload.vendor_id, **preview)
