"""
AI-powered vendor recommendation engine.
Recommends vendors based on event type, location, budget, and ratings.
"""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import math
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def convert_objectids_to_strings(obj: Any) -> Any:
    """
    Recursively convert all ObjectId instances to strings in a document.
    Handles nested dicts, lists, and mixed structures.
    
    Args:
        obj: Any object that might contain ObjectIds
        
    Returns:
        The same object structure with all ObjectIds converted to strings
    """
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_objectids_to_strings(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectids_to_strings(item) for item in obj]
    else:
        return obj


class RecommendationEngine:
    """Generates personalized vendor recommendations using heuristic scoring."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.vendors_collection = db.vendors
        self.bookings_collection = db.bookings
        self.users_collection = db.users

    async def get_recommendations(
        self,
        event_type: str,
        city: str,
        budget_max: float = None,
        budget_min: float = None,
        category: str = None,
        user_id: str = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Generate vendor recommendations based on event parameters.

        Args:
            event_type: Type of event (wedding, corporate, birthday, etc.)
            city: City for the event
            budget_max: Maximum budget in rupees
            budget_min: Minimum budget in rupees
            category: Vendor category (caterer, photographer, etc.)
            user_id: Current user ID for personalization
            limit: Number of recommendations to return

        Returns:
            List of recommended vendors with scores
        """
        try:
            # Build query filters
            query = {"city": {"$regex": city, "$options": "i"}, "status": "active"}

            if category:
                query["category"] = category

            # Get candidate vendors
            candidates = await self.vendors_collection.find(query).to_list(None)

            if not candidates:
                return []

            # Score each vendor
            scored_vendors = []
            for vendor in candidates:
                score = self._calculate_vendor_score(
                    vendor=vendor,
                    event_type=event_type,
                    budget_max=budget_max,
                    budget_min=budget_min,
                    city=city,
                    user_id=user_id,
                )

                if score["total_score"] > 0:
                    # Convert all ObjectIds in the vendor document to strings
                    vendor_clean = convert_objectids_to_strings(vendor)
                    vendor_clean["recommendation_score"] = score["total_score"]
                    vendor_clean["score_breakdown"] = score["breakdown"]
                    scored_vendors.append(vendor_clean)

            # Sort by score and return top recommendations
            scored_vendors.sort(
                key=lambda x: x["recommendation_score"], reverse=True
            )
            return scored_vendors[:limit]

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []

    def _calculate_vendor_score(
        self,
        vendor: Dict[str, Any],
        event_type: str,
        budget_max: float = None,
        budget_min: float = None,
        city: str = None,
        user_id: str = None,
    ) -> Dict[str, Any]:
        """
        Calculate recommendation score for a vendor using multiple factors.
        Returns score breakdown for transparency.
        """
        breakdown = {}
        total_score = 0.0

        # 1. Category match (0-25 points)
        category_score = self._score_category_match(vendor, event_type)
        breakdown["category_match"] = category_score
        total_score += category_score

        # 2. Rating & reviews (0-20 points)
        rating_score = self._score_rating(vendor)
        breakdown["rating"] = rating_score
        total_score += rating_score

        # 3. Budget fitness (0-20 points)
        budget_score = self._score_budget_fitness(
            vendor, budget_min, budget_max
        )
        breakdown["budget_fitness"] = budget_score
        total_score += budget_score

        # 4. Experience & portfolio (0-15 points)
        experience_score = self._score_experience(vendor)
        breakdown["experience"] = experience_score
        total_score += experience_score

        # 5. Availability (0-10 points)
        availability_score = self._score_availability(vendor)
        breakdown["availability"] = availability_score
        total_score += availability_score

        # 6. Location proximity (0-10 points)
        location_score = self._score_location_proximity(vendor, city)
        breakdown["location_proximity"] = location_score
        total_score += location_score

        return {"total_score": total_score, "breakdown": breakdown}

    def _score_category_match(self, vendor: Dict[str, Any], event_type: str) -> float:
        """Score based on vendor category relevance to event type (0-25)."""
        category = (vendor.get("category") or "").lower()
        event_type = (event_type or "").lower()

        # Category-to-event mappings
        mappings = {
            "caterer": ["wedding", "corporate", "birthday", "engagement", "reception"],
            "photographer": ["wedding", "corporate", "birthday", "engagement", "anniversary"],
            "decorator": ["wedding", "corporate", "birthday", "engagement"],
            "dj": ["wedding", "corporate", "party", "birthday"],
            "makeup": ["wedding", "engagement", "party"],
            "venue": ["wedding", "corporate", "birthday"],
        }

        relevant_events = mappings.get(category, [])
        if event_type in relevant_events:
            return 25.0
        elif relevant_events:  # Category exists but not perfect match
            return 15.0
        else:
            return 5.0  # Generic match

    def _score_rating(self, vendor: Dict[str, Any]) -> float:
        """Score based on average rating and review count (0-20)."""
        avg_rating = vendor.get("avg_rating", 0)
        review_count = vendor.get("review_count", 0)

        # Normalize rating (0-5) to 0-15 points
        rating_points = (avg_rating / 5.0) * 15.0 if avg_rating > 0 else 0

        # Bonus for having multiple reviews (0-5 points)
        review_bonus = 0
        if review_count >= 50:
            review_bonus = 5.0
        elif review_count >= 20:
            review_bonus = 3.0
        elif review_count >= 5:
            review_bonus = 1.0

        return min(20.0, rating_points + review_bonus)

    def _score_budget_fitness(
        self,
        vendor: Dict[str, Any],
        budget_min: float = None,
        budget_max: float = None,
    ) -> float:
        """Score based on vendor price range fit with user budget (0-20)."""
        vendor_min = vendor.get("min_price", 0)
        vendor_max = vendor.get("max_price", float("inf"))

        if not budget_max:
            return 10.0  # No budget specified, neutral score

        # Check if vendor's price range overlaps with user budget
        if vendor_min > budget_max:
            return 0  # Too expensive
        elif vendor_max < (budget_min or 0):
            return 0  # Too cheap (unlikely to match quality)
        else:
            # Calculate overlap percentage
            budget_range = (budget_max - (budget_min or 0)) or 1
            overlap_start = max(vendor_min, budget_min or 0)
            overlap_end = min(vendor_max, budget_max)
            overlap = max(0, overlap_end - overlap_start)

            overlap_percentage = min(1.0, overlap / budget_range)
            return overlap_percentage * 20.0

    def _score_experience(self, vendor: Dict[str, Any]) -> float:
        """Score based on years of experience and portfolio size (0-15)."""
        years_exp = vendor.get("years_of_experience", 0)
        portfolio_count = vendor.get("portfolio_count", 0)

        # Years of experience: 0-10 points
        exp_points = min(10.0, (years_exp / 10.0) * 10.0)

        # Portfolio count: 0-5 points
        portfolio_points = 0
        if portfolio_count >= 100:
            portfolio_points = 5.0
        elif portfolio_count >= 50:
            portfolio_points = 3.5
        elif portfolio_count >= 20:
            portfolio_points = 2.0
        elif portfolio_count >= 5:
            portfolio_points = 1.0

        return min(15.0, exp_points + portfolio_points)

    def _score_availability(self, vendor: Dict[str, Any]) -> float:
        """Score based on vendor availability status (0-10)."""
        is_available = vendor.get("is_available", True)
        response_time_hours = vendor.get("avg_response_time_hours", 24)

        base_score = 10.0 if is_available else 0

        # Bonus for fast response time
        if response_time_hours <= 4:
            base_score = min(10.0, base_score + 2.0)
        elif response_time_hours <= 8:
            base_score = min(10.0, base_score + 1.0)

        return base_score

    def _score_location_proximity(self, vendor: Dict[str, Any], city: str) -> float:
        """Score based on location proximity (0-10)."""
        vendor_city = (vendor.get("city") or "").lower()
        search_city = (city or "").lower()

        if vendor_city == search_city:
            return 10.0

        # Same state/region with different city
        vendor_state = (vendor.get("state") or "").lower()
        search_state = (city or "").lower()  # Simplified - in real app would parse state

        if vendor_state == search_state:
            return 5.0

        return 2.0  # Different region

    async def get_personalized_recommendations(
        self,
        user_id: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get personalized recommendations based on user's past behavior.
        """
        try:
            # Get user's booking history
            # user_id can be a string (e.g., "usr_xxxxx") or a valid ObjectId hex string
            query = {}
            try:
                # Try to use as ObjectId if it's a valid hex string
                if len(user_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in user_id):
                    query["user_id"] = ObjectId(user_id)
                else:
                    # Use as string (e.g., "usr_xxxxx")
                    query["user_id"] = user_id
            except (ValueError, TypeError):
                # Fall back to string
                query["user_id"] = user_id
            
            user_bookings = await self.bookings_collection.find(query).to_list(None)

            if not user_bookings:
                # No booking history, return generic top-rated vendors
                recommendations = await self.db.vendors.find(
                    {"status": "active"}
                ).sort([("avg_rating", -1)]).limit(limit).to_list(None)
                # Convert all ObjectIds to strings for JSON serialization
                return [convert_objectids_to_strings(rec) for rec in recommendations]

            # Extract preferences from booking history
            favorite_categories = {}
            favorite_cities = {}

            for booking in user_bookings:
                # Count category preferences
                category = booking.get("vendor_category")
                if category:
                    favorite_categories[category] = (
                        favorite_categories.get(category, 0) + 1
                    )

                # Count city preferences
                booking_city = booking.get("city")
                if booking_city:
                    favorite_cities[booking_city] = (
                        favorite_cities.get(booking_city, 0) + 1
                    )

            # Get top preference
            top_category = (
                max(favorite_categories.items(), key=lambda x: x[1])[0]
                if favorite_categories
                else None
            )
            top_city = (
                max(favorite_cities.items(), key=lambda x: x[1])[0]
                if favorite_cities
                else None
            )

            # Generate recommendations
            query = {"status": "active"}
            if top_category:
                query["category"] = top_category
            if top_city:
                query["city"] = top_city

            recommendations = await self.db.vendors.find(
                query
            ).sort([("avg_rating", -1)]).limit(limit).to_list(None)
            
            # Convert all ObjectIds to strings for JSON serialization
            return [convert_objectids_to_strings(rec) for rec in recommendations]

        except Exception as e:
            logger.error(f"Error getting personalized recommendations: {e}")
            return []

    async def get_trending_vendors(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get trending vendors (most booked in last 30 days).
        """
        try:
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)

            # Pipeline to get vendors booked most recently
            pipeline = [
                {
                    "$match": {
                        "created_at": {"$gte": thirty_days_ago},
                        "status": {"$in": ["confirmed", "completed"]},
                    }
                },
                {"$group": {"_id": "$vendor_id", "booking_count": {"$sum": 1}}},
                {"$sort": {"booking_count": -1}},
                {"$limit": limit},
                {
                    "$lookup": {
                        "from": "vendors",
                        "localField": "_id",
                        "foreignField": "_id",
                        "as": "vendor",
                    }
                },
                {"$unwind": "$vendor"},
            ]

            trending = await self.bookings_collection.aggregate(
                pipeline
            ).to_list(None)
            
            # Convert all ObjectIds to strings for JSON serialization
            vendors = [convert_objectids_to_strings(t.get("vendor", {})) for t in trending]
            return vendors

        except Exception as e:
            logger.error(f"Error getting trending vendors: {e}")
            return []
