from __future__ import annotations

from fastapi import Depends
from fastapi import Header, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from ai_core.module import AIModule
from app.core.config import Settings, get_settings
from app.db import get_db
from app.services.availability_service import AvailabilityService
from app.services.decision_service import DecisionService
from app.services.decision_model_service import DecisionModelService
from app.services.decision_outcome_service import DecisionOutcomeService
from app.services.escrow_service import EscrowService
from app.services.feature_monitor_service import FeatureMonitorService
from app.services.market_signal_service import MarketSignalService
from app.services.negotiation_service import NegotiationService
from app.services.planning_service import PlanningService
from app.services.pricing_service import PricingService
from app.services.profit_monitor_service import ProfitMonitorService
from app.services.risk_service import RiskService
from app.services.trust_service import TrustService
from app.services.vendor_analytics_service import VendorAnalyticsService


def get_planning_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> PlanningService:
    return PlanningService(db)


def get_availability_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> AvailabilityService:
    return AvailabilityService(db)


def get_pricing_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> PricingService:
    return PricingService(db)


def get_trust_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> TrustService:
    return TrustService(db)


def get_vendor_analytics_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> VendorAnalyticsService:
    return VendorAnalyticsService(db)


def get_decision_model_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> DecisionModelService:
    return DecisionModelService(db)


def get_risk_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> RiskService:
    return RiskService(db)


def get_market_signal_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> MarketSignalService:
    return MarketSignalService(db)


def get_feature_monitor_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> FeatureMonitorService:
    return FeatureMonitorService(db)


def get_profit_monitor_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> ProfitMonitorService:
    return ProfitMonitorService(db)


def get_negotiation_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
    settings: Settings = Depends(get_settings),
    vendor_analytics_service: VendorAnalyticsService = Depends(get_vendor_analytics_service),
) -> NegotiationService:
    return NegotiationService(db, settings, vendor_analytics_service)


def get_ai_module_with_services(
    db: AsyncIOMotorDatabase = Depends(get_db),
    settings: Settings = Depends(get_settings),
    pricing_service: PricingService = Depends(get_pricing_service),
    availability_service: AvailabilityService = Depends(get_availability_service),
    trust_service: TrustService = Depends(get_trust_service),
    negotiation_service: NegotiationService = Depends(get_negotiation_service),
    decision_model_service: DecisionModelService = Depends(get_decision_model_service),
    risk_service: RiskService = Depends(get_risk_service),
    market_signal_service: MarketSignalService = Depends(get_market_signal_service),
    feature_monitor_service: FeatureMonitorService = Depends(get_feature_monitor_service),
    profit_monitor_service: ProfitMonitorService = Depends(get_profit_monitor_service),
) -> AIModule:
    decision_service = DecisionService(
        db=db,
        settings=settings,
        pricing_service=pricing_service,
        availability_service=availability_service,
        trust_service=trust_service,
        negotiation_service=negotiation_service,
        decision_model_service=decision_model_service,
        risk_service=risk_service,
        market_signal_service=market_signal_service,
    )
    return AIModule(
        db=db,
        decision_service=decision_service,
        decision_model_service=decision_model_service,
        risk_service=risk_service,
        feature_monitor_service=feature_monitor_service,
        profit_monitor_service=profit_monitor_service,
    )


async def guard_ai_route(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ai_module: AIModule = Depends(get_ai_module_with_services),
):
    return await ai_module.control_plane.guard_request(request=request, api_key=x_api_key)


def get_decision_outcome_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
    vendor_analytics_service: VendorAnalyticsService = Depends(get_vendor_analytics_service),
    profit_monitor_service: ProfitMonitorService = Depends(get_profit_monitor_service),
) -> DecisionOutcomeService:
    return DecisionOutcomeService(db, vendor_analytics_service, profit_monitor_service)


def get_escrow_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
    decision_outcome_service: DecisionOutcomeService = Depends(get_decision_outcome_service),
    vendor_analytics_service: VendorAnalyticsService = Depends(get_vendor_analytics_service),
) -> EscrowService:
    return EscrowService(db, decision_outcome_service, vendor_analytics_service)


def get_decision_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
    settings: Settings = Depends(get_settings),
    pricing_service: PricingService = Depends(get_pricing_service),
    availability_service: AvailabilityService = Depends(get_availability_service),
    trust_service: TrustService = Depends(get_trust_service),
    negotiation_service: NegotiationService = Depends(get_negotiation_service),
    decision_model_service: DecisionModelService = Depends(get_decision_model_service),
    risk_service: RiskService = Depends(get_risk_service),
    market_signal_service: MarketSignalService = Depends(get_market_signal_service),
) -> DecisionService:
    return DecisionService(
        db=db,
        settings=settings,
        pricing_service=pricing_service,
        availability_service=availability_service,
        trust_service=trust_service,
        negotiation_service=negotiation_service,
        decision_model_service=decision_model_service,
        risk_service=risk_service,
        market_signal_service=market_signal_service,
    )
