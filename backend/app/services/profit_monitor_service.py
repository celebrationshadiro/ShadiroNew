from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.ai_control_service import AIControlService


class ProfitMonitorService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.ai_control_service = AIControlService(db)

    async def evaluate_profitability(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        since_7d = now - timedelta(days=7)
        baseline_start = now - timedelta(days=14)
        baseline_end = since_7d

        recent_rows = await self.db.decision_outcomes_extended.find(
            {"timestamp": {"$gte": since_7d}},
            projection={"revenue_impact": 1, "dispute_occurred": 1, "gross_revenue": 1, "is_canary": 1},
            limit=50000,
        ).to_list(length=50000)
        baseline_rows = await self.db.decision_outcomes_extended.find(
            {"timestamp": {"$gte": baseline_start, "$lt": baseline_end}},
            projection={"revenue_impact": 1, "dispute_occurred": 1, "gross_revenue": 1},
            limit=50000,
        ).to_list(length=50000)

        last_7d_revenue = sum(float(r.get("revenue_impact", 0.0)) for r in recent_rows)
        last_7d_dispute_cost = sum(
            max(0.0, float(r.get("gross_revenue", 0.0)) - float(r.get("revenue_impact", 0.0)))
            for r in recent_rows
            if bool(r.get("dispute_occurred", False))
        )
        baseline_revenue = sum(float(r.get("revenue_impact", 0.0)) for r in baseline_rows)
        net_profit_delta_vs_baseline = (
            0.0 if abs(baseline_revenue) <= 1e-9 else ((last_7d_revenue - baseline_revenue) / abs(baseline_revenue))
        )

        canary_rows = [r for r in recent_rows if bool(r.get("is_canary", False))]
        active_rows = [r for r in recent_rows if not bool(r.get("is_canary", False))]
        canary_avg = sum(float(r.get("revenue_impact", 0.0)) for r in canary_rows) / max(1, len(canary_rows))
        active_avg = sum(float(r.get("revenue_impact", 0.0)) for r in active_rows) / max(1, len(active_rows))
        canary_vs_active_profit_gap = canary_avg - active_avg

        result = {
            "last_7d_revenue": round(last_7d_revenue, 2),
            "last_7d_dispute_cost": round(last_7d_dispute_cost, 2),
            "net_profit_delta_vs_baseline": round(net_profit_delta_vs_baseline, 6),
            "canary_vs_active_profit_gap": round(canary_vs_active_profit_gap, 6),
        }
        if net_profit_delta_vs_baseline < -0.10:
            cfg = await self.ai_control_service.get_financial_control()
            if bool(cfg.get("auto_freeze_enabled", True)):
                await self.ai_control_service.set_freeze(decision=True)
                await self.db.ai_profit_alerts.insert_one(
                    {
                        "_id": ObjectId(),
                        **result,
                        "alert_type": "negative_profit_delta",
                        "freeze_triggered": True,
                        "timestamp": now,
                    }
                )
        return result

