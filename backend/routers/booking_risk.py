from fastapi import APIRouter, Depends, HTTPException, Request
from auth import require_role
from models import UserRole
from services.risk_engine import compute_cancellation_risk, recommend_refund_action

router = APIRouter(prefix="/api/bookings", tags=["booking-risk"])


@router.get("/{booking_id}/cancellation-risk")
async def get_cancellation_risk(booking_id: str, request: Request, current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.VENDOR]))):
    db = request.app.state.db
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    vendor = None
    if booking.get("vendor_id"):
        vendor = await db.vendors.find_one({"id": booking.get("vendor_id")}, {"_id": 0})

    risk = compute_cancellation_risk(vendor or {}, booking)
    return risk


@router.get("/{booking_id}/refund-recommendation")
async def get_refund_recommendation(booking_id: str, request: Request, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    db = request.app.state.db
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    vendor = None
    if booking.get("vendor_id"):
        vendor = await db.vendors.find_one({"id": booking.get("vendor_id")}, {"_id": 0})

    risk = compute_cancellation_risk(vendor or {}, booking)
    recommendation = recommend_refund_action(risk, booking)
    return {"risk": risk, "recommendation": recommendation}
