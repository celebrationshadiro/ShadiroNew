"""
Professional delivery analytics system.

Provides:
- Admin operational dashboards
- Partner performance metrics
- Real-time heatmaps
- ETA accuracy tracking
- Fraud metrics
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class DeliveryAnalyticsService:
    """
    Comprehensive analytics for Shadiro delivery network.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_admin_dashboard_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        Get admin operational dashboard metrics.
        """
        start_time = start_time or (datetime.now(timezone.utc) - timedelta(hours=24))
        end_time = end_time or datetime.now(timezone.utc)

        query = {
            "created_at": {
                "$gte": start_time,
                "$lte": end_time,
            }
        }

        # Job metrics
        total_jobs = await self.db.jobs.count_documents(query)
        completed = await self.db.jobs.count_documents({**query, "state": "completed"})
        cancelled = await self.db.jobs.count_documents({**query, "state": "cancelled"})
        active = await self.db.jobs.count_documents({**query, "state": "en_route"})

        # ETA accuracy
        eta_pipeline = [
            {"$match": {**query, "state": "completed", "estimated_eta_minutes": {"$exists": True}}},
            {
                "$project": {
                    "eta_accuracy": {
                        "$cond": {
                            "if": {"$gt": ["$actual_duration_minutes", 0]},
                            "then": {
                                "$divide": [
                                    "$estimated_eta_minutes",
                                    "$actual_duration_minutes",
                                ]
                            },
                            "else": 1,
                        }
                    },
                }
            },
            {
                "$group": {
                    "_id": None,
                    "avg_accuracy": {"$avg": "$eta_accuracy"},
                }
            },
        ]

        eta_accuracy = 1.0
        eta_result = await self.db.jobs.aggregate(eta_pipeline).to_list(1)
        if eta_result:
            eta_accuracy = eta_result[0].get("avg_accuracy", 1.0)

        # Partner metrics
        online_partners = await self.db.delivery_partners.count_documents({"is_online": True})
        verified_partners = await self.db.delivery_partners.count_documents(
            {"status": "verified"}
        )

        # Fraud metrics
        fraud_events = await self.db.fraud_events.count_documents(query)
        critical_fraud = await self.db.fraud_events.count_documents(
            {**query, "severity": "critical"}
        )

        return {
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "job_metrics": {
                "total": total_jobs,
                "completed": completed,
                "cancelled": cancelled,
                "active": active,
                "success_rate": completed / max(1, total_jobs),
            },
            "eta_metrics": {
                "accuracy_ratio": round(eta_accuracy, 2),
                "on_time_deliveries": None,  # Calculate if tracked
            },
            "partner_metrics": {
                "online": online_partners,
                "verified": verified_partners,
                "avg_rating": None,  # Aggregate from partners
            },
            "fraud_metrics": {
                "total_events": fraud_events,
                "critical_events": critical_fraud,
                "fraud_rate": fraud_events / max(1, total_jobs),
            },
        }

    async def get_partner_performance_metrics(
        self,
        partner_id: str,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Get performance metrics for individual delivery partner.
        """
        start_time = datetime.now(timezone.utc) - timedelta(days=days)

        query = {
            "partner_id": partner_id,
            "created_at": {"$gte": start_time},
        }

        # Job stats
        total_jobs = await self.db.jobs.count_documents(query)
        completed = await self.db.jobs.count_documents({**query, "state": "completed"})
        cancelled = await self.db.jobs.count_documents({**query, "state": "cancelled"})

        # Earnings
        earnings_pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": None,
                    "total_earnings_paise": {"$sum": "$partner_earnings_paise"},
                }
            },
        ]
        earnings_result = await self.db.jobs.aggregate(earnings_pipeline).to_list(1)
        total_earnings = earnings_result[0].get("total_earnings_paise", 0) if earnings_result else 0

        # Rating
        ratings_pipeline = [
            {"$match": {**query, "partner_rating": {"$exists": True}}},
            {
                "$group": {
                    "_id": None,
                    "avg_rating": {"$avg": "$partner_rating"},
                }
            },
        ]
        ratings_result = await self.db.jobs.aggregate(ratings_pipeline).to_list(1)
        avg_rating = ratings_result[0].get("avg_rating", 0) if ratings_result else 0

        # Get partner document for additional info
        partner = await self.db.delivery_partners.find_one(
            {"id": partner_id},
            {"_id": 0},
        )

        return {
            "partner_id": partner_id,
            "period_days": days,
            "job_stats": {
                "total": total_jobs,
                "completed": completed,
                "cancelled": cancelled,
                "completion_rate": completed / max(1, total_jobs),
            },
            "earnings": {
                "total_paise": total_earnings,
                "total_rupees": total_earnings / 100,
                "avg_per_job_rupees": (total_earnings / 100) / max(1, completed),
            },
            "quality": {
                "avg_rating": round(avg_rating, 2),
                "acceptance_rate": partner.get("acceptance_rate", 0) if partner else 0,
                "cancellation_rate": cancelled / max(1, total_jobs),
            },
            "reliability": {
                "network_reliability": partner.get("network_reliability", 0) if partner else 0,
                "device_uptime": partner.get("device_uptime_percentage", 0) if partner else 0,
            },
        }

    async def get_heatmap_data(
        self,
        hours: int = 1,
        grid_size_meters: int = 500,
    ) -> list[dict[str, Any]]:
        """
        Get delivery heatmap data (active delivery zones).
        
        Returns grid of active delivery activity.
        """
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Get recent job locations
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_time},
                    "pickup.lat": {"$exists": True},
                    "pickup.lng": {"$exists": True},
                    "state": {"$in": ["assigned", "en_route", "completed"]},
                }
            },
            {
                "$group": {
                    "_id": {
                        "lat": {
                            "$toInt": {
                                "$multiply": [
                                    {"$floor": {"$divide": ["$pickup.lat", 0.01]}},
                                    0.01,
                                ]
                            }
                        },
                        "lng": {
                            "$toInt": {
                                "$multiply": [
                                    {"$floor": {"$divide": ["$pickup.lng", 0.01]}},
                                    0.01,
                                ]
                            }
                        },
                    },
                    "count": {"$sum": 1},
                    "avg_rating": {"$avg": "$partner_rating"},
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 1000},
        ]

        heatmap_cells = await self.db.jobs.aggregate(pipeline).to_list(None)

        return [
            {
                "lat": cell["_id"]["lat"],
                "lng": cell["_id"]["lng"],
                "intensity": min(1.0, cell["count"] / 100),
                "delivery_count": cell["count"],
                "avg_rating": round(cell["avg_rating"], 2),
            }
            for cell in heatmap_cells
        ]

    async def get_active_zones(self) -> dict[str, Any]:
        """
        Get currently active delivery zones ranked by activity.
        """
        pipeline = [
            {
                "$match": {
                    "state": "en_route",
                    "created_at": {
                        "$gte": datetime.now(timezone.utc) - timedelta(hours=1)
                    },
                }
            },
            {
                "$group": {
                    "_id": "$pickup.city",
                    "active_deliveries": {"$sum": 1},
                    "avg_eta": {"$avg": "$estimated_eta_minutes"},
                }
            },
            {"$sort": {"active_deliveries": -1}},
        ]

        zones = await self.db.jobs.aggregate(pipeline).to_list(None)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "zones": [
                {
                    "city": zone["_id"],
                    "active_deliveries": zone["active_deliveries"],
                    "avg_eta_minutes": round(zone["avg_eta"], 1),
                }
                for zone in zones
            ],
        }

    async def get_delivery_quality_report(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """
        Comprehensive delivery quality report.
        """
        query = {
            "state": "completed",
            "created_at": {
                "$gte": start_date,
                "$lte": end_date,
            },
        }

        # Calculate various metrics
        total_completed = await self.db.jobs.count_documents(query)

        on_time = await self.db.jobs.count_documents(
            {
                **query,
                "$expr": {
                    "$lte": [
                        "$actual_duration_minutes",
                        {"$multiply": ["$estimated_eta_minutes", 1.1]},
                    ]
                },
            }
        )

        highly_rated = await self.db.jobs.count_documents(
            {
                **query,
                "partner_rating": {"$gte": 4.5},
            }
        )

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "summary": {
                "total_deliveries": total_completed,
                "on_time_rate": on_time / max(1, total_completed),
                "highly_rated_rate": highly_rated / max(1, total_completed),
            },
        }
