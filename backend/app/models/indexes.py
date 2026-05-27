from __future__ import annotations

from pymongo import ASCENDING, DESCENDING, IndexModel


def build_indexes(settings) -> dict[str, list[IndexModel]]:
    return {
        "users": [
            IndexModel([("email", ASCENDING)], unique=True, name="uq_users_email"),
            IndexModel([("role", ASCENDING), ("status", ASCENDING)], name="idx_users_role_status"),
            IndexModel([("created_at", DESCENDING)], name="idx_users_created_at"),
        ],
        "vendors": [
            IndexModel([("owner_user_id", ASCENDING)], unique=True, sparse=True, name="uq_vendors_owner"),
            IndexModel([("status", ASCENDING), ("city", ASCENDING)], name="idx_vendors_status_city"),
            IndexModel([("categories", ASCENDING)], name="idx_vendors_categories"),
        ],
        "vendor_profiles": [
            IndexModel([("vendor_id", ASCENDING)], unique=True, name="uq_vendor_profiles_vendor_id"),
            IndexModel([("service_area.city", ASCENDING), ("service_categories", ASCENDING)], name="idx_vendor_profiles_city_category"),
            IndexModel([("avg_response_time_minutes", ASCENDING)], sparse=True, name="idx_vendor_profiles_response_time"),
        ],
        "vendor_availability": [
            IndexModel([("vendor_id", ASCENDING), ("service_date", ASCENDING), ("slot_start", ASCENDING)], unique=True, name="uq_vendor_availability_slot"),
            IndexModel([("service_date", ASCENDING), ("is_available", ASCENDING), ("city", ASCENDING)], name="idx_vendor_availability_lookup"),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, sparse=True, name="ttl_vendor_availability_expires"),
        ],
        "events": [
            IndexModel([("user_id", ASCENDING), ("event_date", ASCENDING)], name="idx_events_user_date"),
            IndexModel([("status", ASCENDING), ("event_date", ASCENDING)], name="idx_events_status_date"),
            IndexModel([("created_at", DESCENDING)], name="idx_events_created_at"),
        ],
        "event_plans": [
            IndexModel([("event_id", ASCENDING), ("version", DESCENDING)], unique=True, name="uq_event_plans_event_version"),
            IndexModel([("user_id", ASCENDING), ("updated_at", DESCENDING)], name="idx_event_plans_user_updated"),
        ],
        "quotes": [
            IndexModel([("event_id", ASCENDING), ("vendor_id", ASCENDING), ("status", ASCENDING)], name="idx_quotes_event_vendor_status"),
            IndexModel(
                [("event_id", ASCENDING), ("vendor_id", ASCENDING)],
                unique=True,
                partialFilterExpression={"status": {"$in": ["pending", "accepted"]}},
                name="uq_quotes_active_event_vendor",
            ),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, sparse=True, name="ttl_quotes_expires"),
        ],
        "bookings": [
            IndexModel([("event_id", ASCENDING), ("status", ASCENDING)], name="idx_bookings_event_status"),
            IndexModel([("vendor_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)], name="idx_bookings_vendor_status_created"),
            IndexModel(
                [("event_id", ASCENDING)],
                unique=True,
                partialFilterExpression={"status": {"$in": ["pending", "confirmed", "in_progress"]}},
                name="uq_bookings_one_active_per_event",
            ),
        ],
        "milestones": [
            IndexModel([("booking_id", ASCENDING), ("sequence", ASCENDING)], unique=True, name="uq_milestones_booking_sequence"),
            IndexModel([("booking_id", ASCENDING), ("status", ASCENDING)], name="idx_milestones_booking_status"),
            IndexModel([("due_at", ASCENDING), ("status", ASCENDING)], name="idx_milestones_due_status"),
        ],
        "escrow_transactions": [
            IndexModel([("booking_id", ASCENDING), ("milestone_id", ASCENDING), ("tx_type", ASCENDING)], name="idx_escrow_booking_milestone_type"),
            IndexModel([("status", ASCENDING), ("created_at", DESCENDING)], name="idx_escrow_status_created"),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, sparse=True, name="ttl_escrow_expires"),
        ],
        "negotiations": [
            IndexModel([("event_id", ASCENDING), ("vendor_id", ASCENDING), ("status", ASCENDING)], name="idx_negotiations_event_vendor_status"),
            IndexModel([("vendor_id", ASCENDING), ("last_activity_at", DESCENDING)], name="idx_negotiations_vendor_activity"),
            IndexModel(
                [("expires_at", ASCENDING)],
                expireAfterSeconds=0,
                sparse=True,
                name="ttl_negotiations_expires",
            ),
        ],
        "trust_scores": [
            IndexModel([("vendor_id", ASCENDING)], unique=True, name="uq_trust_scores_vendor_id"),
            IndexModel([("score", DESCENDING), ("updated_at", DESCENDING)], name="idx_trust_scores_score_updated"),
        ],
        "vendor_analytics": [
            IndexModel([("vendor_id", ASCENDING), ("day", ASCENDING)], unique=True, name="uq_vendor_analytics_vendor_day"),
            IndexModel([("category", ASCENDING), ("day", DESCENDING)], name="idx_vendor_analytics_category_day"),
        ],
        "decision_scores": [
            IndexModel([("event_id", ASCENDING), ("vendor_id", ASCENDING)], unique=True, name="uq_decision_event_vendor"),
            IndexModel([("score", DESCENDING), ("created_at", DESCENDING)], name="idx_decision_scores_rank"),
            IndexModel([("model_version", DESCENDING), ("created_at", DESCENDING)], name="idx_decision_scores_model_created"),
            IndexModel([("risk_version", DESCENDING), ("created_at", DESCENDING)], name="idx_decision_scores_risk_created"),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, sparse=True, name="ttl_decision_scores_expires"),
        ],
        "decision_outcomes": [
            IndexModel([("decision_id", ASCENDING)], unique=True, sparse=True, name="uq_decision_outcomes_decision_id"),
            IndexModel([("booking_id", ASCENDING)], unique=True, name="uq_decision_outcomes_booking_id"),
            IndexModel([("model_version", DESCENDING), ("created_at", DESCENDING)], name="idx_decision_outcomes_model_created"),
            IndexModel([("actual_completion_status", ASCENDING), ("actual_dispute_flag", ASCENDING)], name="idx_decision_outcomes_status_dispute"),
        ],
        "decision_outcomes_extended": [
            IndexModel([("booking_id", ASCENDING)], unique=True, name="uq_decision_outcomes_ext_booking"),
            IndexModel([("model_version", DESCENDING), ("timestamp", DESCENDING)], name="idx_decision_outcomes_ext_model_timestamp"),
            IndexModel([("risk_version", DESCENDING), ("timestamp", DESCENDING)], name="idx_decision_outcomes_ext_risk_timestamp"),
            IndexModel([("is_canary", ASCENDING), ("timestamp", DESCENDING)], name="idx_decision_outcomes_ext_canary_timestamp"),
        ],
        "decision_model_config": [
            IndexModel([("model_version", DESCENDING)], unique=True, name="uq_decision_model_version"),
            IndexModel([("active_flag", ASCENDING), ("created_at", DESCENDING)], name="idx_decision_model_active_created"),
            IndexModel([("created_at", DESCENDING)], name="idx_decision_model_created"),
            IndexModel([("active_version", DESCENDING), ("updated_at", DESCENDING)], sparse=True, name="idx_decision_model_control_active"),
        ],
        "calibration_audit_logs": [
            IndexModel([("model_version_from", DESCENDING), ("created_at", DESCENDING)], name="idx_calibration_audit_version_created"),
            IndexModel([("aborted_flag", ASCENDING), ("created_at", DESCENDING)], name="idx_calibration_audit_aborted_created"),
        ],
        "calibration_locks": [
            IndexModel([("lease_expires_at", ASCENDING)], expireAfterSeconds=0, name="ttl_calibration_lock_lease"),
        ],
        "booking_risk_snapshots": [
            IndexModel([("booking_id", ASCENDING), ("created_at", DESCENDING)], name="idx_booking_risk_booking_created"),
            IndexModel([("vendor_id", ASCENDING), ("created_at", DESCENDING)], name="idx_booking_risk_vendor_created"),
            IndexModel([("risk_version", DESCENDING), ("created_at", DESCENDING)], name="idx_booking_risk_version_created"),
        ],
        "market_signals": [
            IndexModel([("category", ASCENDING), ("city", ASCENDING), ("created_at", DESCENDING)], name="idx_market_signal_lookup"),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, sparse=True, name="ttl_market_signals_expires"),
        ],
        "risk_model_config": [
            IndexModel([("risk_version", DESCENDING)], unique=True, sparse=True, name="uq_risk_model_version"),
            IndexModel([("active_flag", ASCENDING), ("created_at", DESCENDING)], name="idx_risk_model_active_created"),
            IndexModel([("active_version", DESCENDING), ("updated_at", DESCENDING)], sparse=True, name="idx_risk_model_control_active"),
            IndexModel([("canary_version", DESCENDING), ("canary_traffic_percentage", DESCENDING)], sparse=True, name="idx_risk_model_control_canary"),
            IndexModel([("shadow_version", DESCENDING), ("updated_at", DESCENDING)], sparse=True, name="idx_risk_model_control_shadow"),
        ],
        "feature_drift_alerts": [
            IndexModel([("feature_name", ASCENDING), ("created_at", DESCENDING)], name="idx_feature_drift_feature_created"),
            IndexModel([("created_at", DESCENDING)], name="idx_feature_drift_created"),
        ],
        "ai_execution_logs": [
            IndexModel([("model_version", DESCENDING), ("timestamp", DESCENDING)], name="idx_ai_exec_model_timestamp"),
            IndexModel([("request_id", ASCENDING)], unique=True, name="uq_ai_exec_request_id"),
        ],
        "risk_weight_audit_logs": [
            IndexModel([("from_risk_version", DESCENDING), ("created_at", DESCENDING)], name="idx_risk_weight_audit_from_created"),
            IndexModel([("to_risk_version", DESCENDING), ("created_at", DESCENDING)], name="idx_risk_weight_audit_to_created"),
        ],
        "shadow_model_logs": [
            IndexModel([("shadow_version", DESCENDING), ("timestamp", DESCENDING)], name="idx_shadow_model_version_timestamp"),
            IndexModel([("request_id", ASCENDING)], name="idx_shadow_model_request_id"),
        ],
        "ai_profit_alerts": [
            IndexModel([("alert_type", ASCENDING), ("timestamp", DESCENDING)], name="idx_ai_profit_alert_type_timestamp"),
            IndexModel([("timestamp", DESCENDING)], name="idx_ai_profit_alert_timestamp"),
        ],
        "ai_rollback_logs": [
            IndexModel([("model_type", ASCENDING), ("timestamp", DESCENDING)], name="idx_ai_rollback_model_timestamp"),
        ],
        "risk_rebalance_locks": [
            IndexModel([("lease_expires_at", ASCENDING)], expireAfterSeconds=0, name="ttl_risk_rebalance_lock"),
        ],
        "ai_control_config": [
            IndexModel([("updated_at", DESCENDING)], name="idx_ai_control_updated"),
        ],
        "ai_financial_control": [
            IndexModel([("updated_at", DESCENDING)], name="idx_ai_financial_control_updated"),
        ],
        "ai_rate_limits": [
            IndexModel([("principal", ASCENDING), ("window_start", DESCENDING)], name="idx_ai_rate_limit_principal_window"),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, name="ttl_ai_rate_limits_expires"),
        ],
    }


async def ensure_indexes(db, settings) -> None:
    index_map = build_indexes(settings)
    for collection, indexes in index_map.items():
        if indexes:
            await db[collection].create_indexes(indexes)
