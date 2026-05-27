"""
Advanced delivery assignment engine with ML-ready weighted scoring.

Factors considered:
- Live traffic-aware distance
- Partner quality metrics (ratings, completion rate, reliability)
- Dynamic fraud risk scoring
- Battery/device health
- Fair earnings distribution
- Workload balancing
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from shadiro_delivery_network.constants import (
    COLLECTION_JOBS,
    COLLECTION_PARTNERS,
    LogisticsTier,
    PartnerStatus,
)

logger = logging.getLogger(__name__)


class AdvancedAssignmentEngine:
    """
    ML-ready assignment engine with weighted multi-factor scoring.
    Extensible for ML model integration.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def calculate_partner_score(
        self,
        partner: dict[str, Any],
        job: dict[str, Any],
        *,
        traffic_factor: float = 1.0,
        eta_minutes: Optional[float] = None,
        live_congestion_level: Optional[str] = None,
    ) -> dict[str, float]:
        """
        Calculate comprehensive assignment score for a partner.

        Returns:
            {
                'total_score': float,
                'distance_score': float,
                'quality_score': float,
                'reliability_score': float,
                'fraud_score': float,
                'earnings_fairness_score': float,
                'workload_score': float,
            }
        """
        from shadiro_delivery_network.assignment_engine import haversine_km

        # 1. DISTANCE & TRAFFIC SCORE (25%)
        pickup = job.get("pickup") or {}
        plat = float(pickup.get("lat") or 19.076)
        plng = float(pickup.get("lng") or 72.8777)

        partner_lat = partner.get("last_lat")
        partner_lng = partner.get("last_lng")

        if partner_lat is not None and partner_lng is not None:
            distance_km = haversine_km(
                float(partner_lat),
                float(partner_lng),
                plat,
                plng,
            )
        else:
            distance_km = 50.0

        # Apply traffic factor for live ETA
        if live_congestion_level == "heavy":
            distance_km *= 1.4
        elif live_congestion_level == "moderate":
            distance_km *= 1.2

        distance_score = max(0, 100 - (distance_km * 2)) / 100  # 0-1
        distance_score *= 25  # Weight: 25%

        # 2. PARTNER QUALITY SCORE (30%)
        rating = float(partner.get("rating_avg") or 4.2) / 5.0  # Normalize to 0-1
        completion_rate = float(partner.get("acceptance_rate") or 0.85)
        positive_reviews = int(partner.get("positive_reviews_count") or 0)
        total_deliveries = int(partner.get("total_deliveries_completed" or 0))

        # Review quality multiplier
        review_quality = min(1.0, positive_reviews / max(1, total_deliveries))

        quality_score = (rating * 0.4 + completion_rate * 0.4 + review_quality * 0.2)
        quality_score *= 30  # Weight: 30%

        # 3. RELIABILITY SCORE (20%)
        network_reliability = float(partner.get("network_reliability") or 0.9)
        uptime_percentage = float(partner.get("device_uptime_percentage" or 0.95))
        avg_response_time = float(partner.get("avg_response_time_seconds") or 5.0)

        # Response time component (faster is better, cap at 60s)
        response_score = max(0, 1 - (avg_response_time / 60.0))

        reliability_score = (
            network_reliability * 0.4
            + uptime_percentage * 0.4
            + response_score * 0.2
        )
        reliability_score *= 20  # Weight: 20%

        # 4. FRAUD RISK SCORE (15%) - Lower fraud = higher score
        fraud_score = float(partner.get("fraud_score") or 0.0)  # 0-1
        gps_anomalies = int(partner.get("gps_anomalies_detected") or 0)
        device_risk_level = str(partner.get("device_risk_level") or "low").lower()
        
        device_risk_map = {"low": 0.95, "medium": 0.6, "high": 0.2}
        device_risk_score = device_risk_map.get(device_risk_level, 0.95)

        fraud_risk_score = (
            (1 - fraud_score) * 0.5
            + device_risk_score * 0.3
            + max(0, 1 - (gps_anomalies / 10.0)) * 0.2
        )
        fraud_risk_score *= 15  # Weight: 15%

        # 5. EARNINGS FAIRNESS SCORE (5%)
        # Partner with lower recent earnings gets slight boost
        recent_earnings_paise = int(partner.get("earnings_today_paise") or 0)
        daily_target_paise = 100000  # ₹1000

        if recent_earnings_paise < daily_target_paise:
            earnings_fairness = 1.0
        else:
            # Penalize gradually as earnings increase
            earnings_fairness = max(0.3, 1 - (recent_earnings_paise - daily_target_paise) / (daily_target_paise * 2))

        earnings_fairness_score = earnings_fairness * 5  # Weight: 5%

        # 6. WORKLOAD BALANCE SCORE (5%)
        active_jobs = int(partner.get("active_job_count") or 0)
        max_concurrent_jobs = int(partner.get("max_concurrent_jobs") or 5)
        
        if active_jobs == 0:
            workload_score = 1.0
        elif active_jobs >= max_concurrent_jobs:
            workload_score = 0.1
        else:
            workload_score = 1 - (active_jobs / max_concurrent_jobs)

        workload_score *= 5  # Weight: 5%

        # Calculate total
        total_score = (
            distance_score
            + quality_score
            + reliability_score
            + fraud_risk_score
            + earnings_fairness_score
            + workload_score
        )

        return {
            "total_score": total_score,
            "distance_score": distance_score,
            "quality_score": quality_score,
            "reliability_score": reliability_score,
            "fraud_score": fraud_risk_score,
            "earnings_fairness_score": earnings_fairness_score,
            "workload_score": workload_score,
        }

    async def rank_partners_advanced(
        self,
        candidates: list[dict[str, Any]],
        job: dict[str, Any],
        *,
        limit: int = 25,
        live_traffic_data: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """
        Rank candidates using advanced multi-factor scoring.
        
        Args:
            candidates: List of eligible partners
            job: Delivery job details
            limit: Max candidates to return
            live_traffic_data: Live traffic conditions (from Google Maps API)
            
        Returns:
            Sorted list of top candidates with scores
        """
        ranked = []
        
        for partner in candidates:
            # Extract traffic factor
            congestion = None
            if live_traffic_data:
                congestion = live_traffic_data.get("congestion_level")

            scores = await self.calculate_partner_score(
                partner,
                job,
                live_congestion_level=congestion,
            )

            ranked.append({
                **partner,
                **scores,  # Flatten score dict
                "_score_breakdown": {k: v for k, v in scores.items() if k != "total_score"},
            })

        # Sort by total score descending
        ranked.sort(key=lambda x: float(x.get("total_score") or 0), reverse=True)
        return ranked[:limit]

    async def get_assignment_explain(
        self,
        partner: dict[str, Any],
        job: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Get human-readable explanation for why partner was assigned.
        Useful for transparency and debugging.
        """
        scores = await self.calculate_partner_score(partner, job)

        breakdown = scores.pop("_score_breakdown", {})
        reasons = []

        if scores.get("distance_score", 0) > 20:
            reasons.append("Closest to pickup location")
        if scores.get("quality_score", 0) > 25:
            reasons.append("High ratings and completion rate")
        if scores.get("reliability_score", 0) > 15:
            reasons.append("Excellent network reliability")
        if scores.get("workload_score", 0) > 4:
            reasons.append("Good availability for new jobs")

        return {
            "partner_id": partner.get("id"),
            "total_score": scores.get("total_score", 0),
            "scores": breakdown,
            "reasons": reasons,
        }
