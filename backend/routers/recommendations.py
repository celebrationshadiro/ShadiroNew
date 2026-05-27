"""
Recommendation engine API endpoints.
Provides personalized vendor recommendations based on event parameters.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from core.security import get_current_user
from core.database import get_db_from_request
from services import RecommendationEngine
from typing import Optional

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


def get_recommendation_engine(
    db: AsyncIOMotorDatabase = Depends(get_db_from_request),
):
    """Dependency to get recommendation engine instance."""
    return RecommendationEngine(db)


def wrap(data):
    """Wrap response data for consistency with axios client."""
    return {"data": data}


@router.get(
    "",
    description="Authenticated endpoint: requires logged-in user token.",
)
async def get_vendor_recommendations(
    event_type: str = Query(..., description="Type of event (wedding, corporate, etc.)"),
    city: str = Query(..., description="City for the event"),
    budget_max: Optional[float] = Query(None, description="Maximum budget in rupees"),
    budget_min: Optional[float] = Query(None, description="Minimum budget in rupees"),
    category: Optional[str] = Query(None, description="Vendor category (caterer, photographer, etc.)"),
    limit: int = Query(5, description="Number of recommendations to return", ge=1, le=20),
    engine: RecommendationEngine = Depends(get_recommendation_engine),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get vendor recommendations based on event parameters.

    This endpoint analyzes event requirements and returns ranked vendor recommendations
    based on category match, ratings, budget fit, experience, availability, and location.

    **Parameters:**
    - `event_type`: Type of event (wedding, corporate, birthday, engagement, anniversary, etc.)
    - `city`: City where the event will take place
    - `budget_max`: Maximum budget in rupees (optional)
    - `budget_min`: Minimum budget in rupees (optional)
    - `category`: Specific vendor category to filter (optional)
    - `limit`: Number of recommendations (1-20, default 5)

    **Returns:**
    Array of vendors ranked by recommendation score, including:
    - Vendor details (name, category, ratings, price range)
    - `recommendation_score`: Composite score (0-100)
    - `score_breakdown`: Component scores for transparency
    """
    try:
        recommendations = await engine.get_recommendations(
            event_type=event_type,
            city=city,
            budget_max=budget_max,
            budget_min=budget_min,
            category=category,
            user_id=str(current_user["id"]),
            limit=limit,
        )
        return wrap(recommendations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


@router.get("/personalized")
async def get_personalized_recommendations(
    limit: int = Query(5, description="Number of recommendations to return", ge=1, le=20),
    engine: RecommendationEngine = Depends(get_recommendation_engine),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get personalized vendor recommendations based on user's booking history.

    Analyzes the user's past bookings to identify preferred vendors, categories, and locations,
    then recommends similar vendors they might like.

    **Parameters:**
    - `limit`: Number of recommendations (1-20, default 5)

    **Returns:**
    Array of personalized vendor recommendations based on user preferences.
    """
    try:
        recommendations = await engine.get_personalized_recommendations(
            user_id=str(current_user["id"]),
            limit=limit,
        )
        return wrap(recommendations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating personalized recommendations: {str(e)}")


@router.get(
    "/trending",
    description="Public endpoint: authentication is not required.",
)
async def get_trending_vendors(
    limit: int = Query(5, description="Number of trending vendors to return", ge=1, le=20),
    engine: RecommendationEngine = Depends(get_recommendation_engine),
) -> dict:
    """
    Get trending vendors (most booked in last 30 days).

    Returns vendors who have received the most bookings in the last 30 days,
    indicating popularity and reliability.

    **Parameters:**
    - `limit`: Number of trending vendors (1-20, default 5)

    **Returns:**
    Array of trending vendors ranked by booking frequency.
    """
    try:
        trending = await engine.get_trending_vendors(limit=limit)
        return wrap(trending)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trending vendors: {str(e)}")
