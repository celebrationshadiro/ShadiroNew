from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import Settings
from app.models.schemas import AvailabilityRequest, DecisionRequest, DecisionResponse, PricingRequest, TrustScoreRequest
from app.services.ai_control_service import AIControlService
from app.services.availability_service import AvailabilityService
from app.services.feature_monitor_service import FeatureMonitorService
from app.services.decision_model_service import DecisionModelService
from app.services.market_signal_service import MarketSignalService
from app.services.negotiation_service import NegotiationService
from app.services.pricing_service import PricingService
from app.services.risk_service import RiskService
from app.services.trust_service import TrustService
from app.utils.ids import oid

logger = logging.getLogger(__name__)


class DecisionService:
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        settings: Settings,
        pricing_service: PricingService,
        availability_service: AvailabilityService,
        trust_service: TrustService,
        negotiation_service: NegotiationService,
        decision_model_service: DecisionModelService,
        risk_service: RiskService,
        market_signal_service: MarketSignalService,
    ) -> None:
        self.db = db
        self.settings = settings
        self.pricing_service = pricing_service
        self.availability_service = availability_service
        self.trust_service = trust_service
        self.negotiation_service = negotiation_service
        self.decision_model_service = decision_model_service
        self.risk_service = risk_service
        self.market_signal_service = market_signal_service
        self.ai_control_service = AIControlService(db)
        self.feature_monitor_service = FeatureMonitorService(db)

    @staticmethod
    def _recommendation(score: int, negotiation_probability: float, demand_pressure: float) -> str:
        if score >= 75 and demand_pressure >= 0.55:
            return "book_now"
        if negotiation_probability >= 0.65 and score < 75:
            return "counter"
        return "wait"

    async def _validate_financial_controls(self) -> None:
        cfg = await self.ai_control_service.get_financial_control()
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=1)
        pipeline = [
            {"$match": {"created_at": {"$gte": since}}},
            {"$group": {"_id": None, "risk_exposure": {"$sum": "$dispute_risk_score"}}},
        ]
        rows = await self.db.booking_risk_snapshots.aggregate(pipeline, allowDiskUse=True).to_list(length=1)
        risk_exposure = float(rows[0].get("risk_exposure", 0.0)) if rows else 0.0

        dispute_rows = await self.db.decision_outcomes.find(
            {"created_at": {"$gte": since}},
            projection={"actual_dispute_flag": 1},
            limit=10000,
        ).to_list(length=10000)
        dispute_rate = (
            sum(1 for r in dispute_rows if bool(r.get("actual_dispute_flag", False))) / max(1, len(dispute_rows))
        )

        max_daily_risk_exposure = float(cfg.get("max_daily_risk_exposure", 100000.0))
        max_dispute_rate = float(cfg.get("max_dispute_rate", 0.15))
        if risk_exposure > max_daily_risk_exposure or dispute_rate > max_dispute_rate:
            if bool(cfg.get("auto_freeze_enabled", True)):
                await self.ai_control_service.set_freeze(decision=True)
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Financial safety threshold breached")

    async def compute_book_now_score(self, payload: DecisionRequest) -> DecisionResponse:
        started = time.perf_counter()
        request_id = payload.request_id or uuid.uuid4().hex
        fallback_used = False
        if await self.ai_control_service.is_frozen("decision"):
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Decision model is frozen")
        await self._validate_financial_controls()

        try:
            model = await self.decision_model_service.get_active_model()
        except Exception as exc:
            logger.exception("decision_model_fetch_failed err=%s", str(exc))
            model = {"model_version": 1, "weights": {}}
            fallback_used = True
        weights = model.get("weights", {})
        price_weight = float(weights.get("price_weight", 0.28))
        availability_weight = float(weights.get("availability_weight", 0.24))
        trust_weight = float(weights.get("trust_weight", 0.22))
        demand_weight = float(weights.get("demand_weight", 0.14))
        negotiation_weight = float(weights.get("negotiation_weight", 0.12))

        price = await self.pricing_service.compute_price_fairness(
            PricingRequest(
                event_id=payload.event_id,
                vendor_id=payload.vendor_id,
                category=payload.category,
                quoted_price=payload.quoted_price,
                attendee_count=payload.attendee_count,
                city=payload.city,
            )
        )
        availability = await self.availability_service.check_realtime_availability(
            AvailabilityRequest(
                event_id=payload.event_id,
                category=payload.category,
                city=payload.city,
                start_at=payload.start_at,
                end_at=payload.end_at,
                vendor_ids=[payload.vendor_id],
            )
        )
        trust = await self.trust_service.compute_trust_score(TrustScoreRequest(vendor_id=payload.vendor_id, event_id=payload.event_id))
        negotiation_probability = await self.negotiation_service.get_current_probability(
            event_id=payload.event_id,
            vendor_id=payload.vendor_id,
            fallback_price=payload.quoted_price,
        )

        try:
            market_signal = await self.market_signal_service.get_market_signal(payload.category, payload.city)
            demand_pressure = float(market_signal.get("demand_pressure", 0.5))
        except Exception as exc:
            logger.exception("market_signal_fetch_failed err=%s", str(exc))
            fallback_used = True
            event_id = oid(payload.event_id)
            demand_pipeline = [
                {"$match": {"event_id": event_id, "status": {"$in": ["pending", "accepted"]}}},
                {"$group": {"_id": "$vendor_id", "quote_count": {"$sum": 1}}},
            ]
            demand_rows = await self.db.quotes.aggregate(demand_pipeline).to_list(length=1000)
            active_vendors = max(1, len(demand_rows))
            total_quotes = sum(int(row.get("quote_count", 0)) for row in demand_rows)
            demand_pressure = min(1.0, total_quotes / max(1.0, active_vendors * 3.0))
            market_signal = {"demand_pressure": demand_pressure}

        availability_confidence = (
            float(availability["vendors"][0]["availability_confidence"]) if availability["vendors"] else 0.0
        )
        vendor_behavior = await self.db.vendor_analytics.find_one(
            {"vendor_id": oid(payload.vendor_id)},
            sort=[("day", -1)],
            projection={
                "avg_response_time": 1,
                "counter_offer_frequency": 1,
                "cancellation_rate": 1,
                "milestone_delay_rate": 1,
                "dispute_ratio": 1,
            },
        )
        trust_score_normalized = float(trust["score"]) / 100.0
        price_fairness_normalized = float(price["price_fairness"]) / 100.0
        behavior_bonus = 0.0
        if vendor_behavior:
            response_factor = max(0.0, min(1.0, 1.0 - (float(vendor_behavior.get("avg_response_time", 120.0)) / 240.0)))
            reliability_factor = 1.0 - min(
                1.0,
                (float(vendor_behavior.get("cancellation_rate", 0.0)) * 0.35)
                + (float(vendor_behavior.get("milestone_delay_rate", 0.0)) * 0.30)
                + (float(vendor_behavior.get("dispute_ratio", 0.0)) * 0.35),
            )
            behavior_bonus = max(-0.05, min(0.05, ((response_factor + reliability_factor) / 2.0 - 0.5) * 0.1))

        weighted_score = (
            (price_fairness_normalized * price_weight)
            + (availability_confidence * availability_weight)
            + (trust_score_normalized * trust_weight)
            + (demand_pressure * demand_weight)
            + (negotiation_probability * negotiation_weight)
            + behavior_bonus
        ) * 100.0
        base_score = max(0, min(100, int(round(weighted_score))))

        booking_key = payload.booking_id if payload.booking_id else f"{payload.event_id}:{payload.vendor_id}"
        try:
            risk_prediction = await self.risk_service.predict_dispute_risk(
                request_id=request_id,
                booking_id=booking_key,
                event_id=payload.event_id,
                vendor_id=oid(payload.vendor_id),
                category=payload.category,
                city=payload.city,
                trust_score=float(trust["score"]),
                negotiation_probability=float(negotiation_probability),
                quoted_price=float(payload.quoted_price),
                demand_pressure=float(demand_pressure),
            )
        except Exception as exc:
            logger.exception("risk_prediction_failed err=%s", str(exc))
            fallback_used = True
            risk_prediction = {
                "dispute_risk_score": 0.0,
                "risk_version": 1,
                "risk_adjustment_weights": {"dispute_risk_weight": 0.18, "demand_urgency_weight": 0.14},
                "signals": {},
                "is_canary": False,
                "fallback_used": True,
            }
        dispute_risk_score = float(risk_prediction["dispute_risk_score"])
        risk_weights = risk_prediction["risk_adjustment_weights"]
        dispute_risk_weight = float(risk_weights.get("dispute_risk_weight", 0.18))
        demand_urgency_weight = float(risk_weights.get("demand_urgency_weight", 0.14))
        risk_adjusted_score_raw = (
            float(base_score)
            - ((dispute_risk_score / 100.0) * dispute_risk_weight * 100.0)
            + (float(demand_pressure) * demand_urgency_weight * 100.0)
        )
        score = max(0, min(100, int(round(risk_adjusted_score_raw))))
        explosion_guard_triggered = False
        if dispute_risk_score > 85.0 and float(demand_pressure) > 0.8:
            score = min(score, 62)
            explosion_guard_triggered = True

        risks: List[str] = []
        explanations: List[str] = []
        if availability_confidence < 0.5:
            risks.append("Availability confidence is low for requested slot.")
        if trust_score_normalized < 0.6:
            risks.append("Vendor trust score is below preferred threshold.")
        if price_fairness_normalized < 0.55:
            risks.append("Quote is materially above fair market baseline.")
        if demand_pressure > 0.7:
            explanations.append("Demand pressure is high; inventory may tighten.")
        explanations.extend(
            [
                f"Base decision score: {base_score}/100",
                f"Price fairness: {price['price_fairness']:.2f}/100",
                f"Availability confidence: {availability_confidence * 100:.2f}%",
                f"Trust score: {trust['score']:.2f}/100",
                f"Negotiation success probability: {negotiation_probability * 100:.2f}%",
                f"Dispute risk score: {dispute_risk_score:.2f}/100",
            ]
        )

        recommendation = self._recommendation(score, negotiation_probability, demand_pressure)
        now = datetime.now(timezone.utc)
        result = {
            "event_id": oid(payload.event_id),
            "vendor_id": oid(payload.vendor_id),
            "score": score,
            "base_decision_score": base_score,
            "risk_adjusted_score": score,
            "components": {
                "price_fairness": round(price["price_fairness"], 2),
                "availability_confidence": round(availability_confidence * 100.0, 2),
                "trust_score": round(float(trust["score"]), 2),
                "demand_pressure": round(demand_pressure * 100.0, 2),
                "negotiation_probability": round(negotiation_probability * 100.0, 2),
                "behavior_adjustment": round(behavior_bonus * 100.0, 2),
                "dispute_risk_score": round(dispute_risk_score, 2),
            },
            "market_signal": {
                "city_surge_index": market_signal.get("city_surge_index"),
                "seasonal_multiplier": market_signal.get("seasonal_multiplier"),
                "availability_shrink_rate": market_signal.get("availability_shrink_rate"),
            },
            "recommendation": recommendation,
            "explanation": explanations,
            "risks": risks,
            "model_version": int(model.get("model_version", 1)),
            "risk_version": int(risk_prediction.get("risk_version", 1)),
            "is_canary": bool(risk_prediction.get("is_canary", False)),
            "risk_weights_used": {
                "dispute_risk_weight": dispute_risk_weight,
                "demand_urgency_weight": demand_urgency_weight,
            },
            "explosion_guard_triggered": explosion_guard_triggered,
            "request_id": request_id,
            "booking_key": booking_key,
            "weights_used": {
                "price_weight": price_weight,
                "availability_weight": availability_weight,
                "trust_weight": trust_weight,
                "demand_weight": demand_weight,
                "negotiation_weight": negotiation_weight,
            },
            "quoted_price": payload.quoted_price,
            "created_at": now,
            "expires_at": now + timedelta(seconds=self.settings.decision_score_ttl_seconds),
        }
        await self.db.decision_scores.update_one(
            {"event_id": result["event_id"], "vendor_id": result["vendor_id"]},
            {"$set": result},
            upsert=True,
        )
        execution_time_ms = round((time.perf_counter() - started) * 1000.0, 3)
        await self.db.ai_execution_logs.update_one(
            {"request_id": request_id},
            {
                "$setOnInsert": {"_id": ObjectId()},
                "$set": {
                    "request_id": request_id,
                    "model_version": int(model.get("model_version", 1)),
                    "risk_version": int(risk_prediction.get("risk_version", 1)),
                    "features_used": {
                        "price_fairness": round(price_fairness_normalized, 6),
                        "availability_confidence": round(availability_confidence, 6),
                        "trust_score": round(trust_score_normalized, 6),
                        "demand_pressure": round(demand_pressure, 6),
                        "city_surge_index": market_signal.get("city_surge_index"),
                        "dispute_risk_score": round(dispute_risk_score / 100.0, 6),
                    },
                    "execution_time_ms": execution_time_ms,
                    "fallback_used": bool(fallback_used or risk_prediction.get("fallback_used", False)),
                    "explosion_guard_triggered": explosion_guard_triggered,
                    "timestamp": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        try:
            await self.feature_monitor_service.evaluate_feature_drift()
        except Exception:
            logger.exception("feature_drift_monitor_failed request_id=%s", request_id)
        logger.info("decision_scored event_id=%s vendor_id=%s score=%s", payload.event_id, payload.vendor_id, score)

        return DecisionResponse(
            score=score,
            explanation=explanations,
            risks=risks,
            recommendation=recommendation,
            components=result["components"],
            model_version=result["model_version"],
            risk_version=result["risk_version"],
            risk_adjusted_score=result["risk_adjusted_score"],
            base_decision_score=result["base_decision_score"],
        )
