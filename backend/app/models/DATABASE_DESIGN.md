# Decision OS MongoDB Design

## users
- Fields: `_id:ObjectId`, `email:str`, `password_hash:str`, `role:str`, `status:str`, `created_at:datetime`, `last_login_at:datetime|null`, `phone:str|null`, `profile:object`
- Indexes: `email(unique)`, `(role,status)`, `(created_at desc)`
- Example:
```json
{
  "_id": "ObjectId('65f...')",
  "email": "planner@client.com",
  "password_hash": "$2b$12$...",
  "role": "customer",
  "status": "active",
  "created_at": "2026-02-25T08:00:00Z"
}
```
- Embedding vs referencing: profile subdoc embedded; bookings/events referenced.
- Scale: shard-friendly by `_id`; login path uses unique email index.

## vendors
- Fields: `_id`, `owner_user_id:ObjectId`, `name:str`, `status:str`, `city:str`, `categories:[str]`, `rating_avg:float`, `rating_count:int`, `created_at`, `updated_at`
- Indexes: `owner_user_id(unique,sparse)`, `(status,city)`, `(categories)`
- Example:
```json
{"name":"Blue Orchid Catering","owner_user_id":"ObjectId('65a...')","status":"active","city":"Austin","categories":["catering"]}
```
- Embedding vs referencing: lightweight identity only; heavy operational data in sibling collections.
- Scale: hot search path by status+city+categories.

## vendor_profiles
- Fields: `_id`, `vendor_id:ObjectId`, `service_categories:[str]`, `service_area:{city,state,country}`, `pricing_config:{min_price,max_discount,auto_counter_rules}`, `capacity:{min,max}`, `avg_response_time_minutes:int`, `updated_at`
- Indexes: `vendor_id(unique)`, `(service_area.city,service_categories)`, `(avg_response_time_minutes sparse)`
- Example:
```json
{"vendor_id":"ObjectId('65b...')","service_area":{"city":"Austin"},"pricing_config":{"min_price":1200,"max_discount":18}}
```
- Embedding vs referencing: one-to-one referenced from vendors to keep core vendor read thin.
- Scale: queryable profile by city/category.

## vendor_availability
- Fields: `_id`, `vendor_id:ObjectId`, `city:str`, `service_date:date`, `slot_start:datetime`, `slot_end:datetime`, `is_available:bool`, `capacity_remaining:int`, `confidence:float`, `source:str`, `updated_at`, `expires_at:datetime|null`
- Indexes: `(vendor_id,service_date,slot_start unique)`, `(service_date,is_available,city)`, `expires_at TTL sparse`
- Example:
```json
{"vendor_id":"ObjectId('65b...')","service_date":"2026-03-10","slot_start":"2026-03-10T16:00:00Z","slot_end":"2026-03-10T20:00:00Z","is_available":true,"capacity_remaining":2,"confidence":0.93}
```
- Embedding vs referencing: separate time-series style collection.
- Scale: high write churn; TTL cleanup for stale slots.

## events
- Fields: `_id`, `user_id:ObjectId`, `title:str`, `event_date:datetime`, `location:{city,state,country}`, `status:str`, `budget:float`, `categories:[str]`, `attendee_count:int`, `created_at`, `updated_at`
- Indexes: `(user_id,event_date)`, `(status,event_date)`, `(created_at desc)`
- Example:
```json
{"user_id":"ObjectId('65f...')","title":"Launch Party","event_date":"2026-05-10T19:00:00Z","status":"planning","budget":25000}
```
- Embedding vs referencing: canonical event root; plans/quotes/bookings reference event.
- Scale: customer dashboard and scheduling filters.

## event_plans
- Fields: `_id`, `event_id:ObjectId`, `user_id:ObjectId`, `version:int`, `ai_plan:{agenda,allocations,recommendations}`, `constraints:object`, `updated_at`
- Indexes: `(event_id,version unique)`, `(user_id,updated_at desc)`
- Example:
```json
{"event_id":"ObjectId('660...')","version":3,"ai_plan":{"allocations":{"catering":8000}}}
```
- Embedding vs referencing: kept separate for version history growth.
- Scale: append-only versions, latest by `version desc`.

## quotes
- Fields: `_id`, `event_id:ObjectId`, `vendor_id:ObjectId`, `amount:float`, `currency:str`, `line_items:[object]`, `status:str`, `valid_until:datetime`, `created_at`, `expires_at`
- Indexes: `(event_id,vendor_id,status)`, partial unique `(event_id,vendor_id)` where status in pending/accepted, `expires_at TTL sparse`
- Example:
```json
{"event_id":"ObjectId('660...')","vendor_id":"ObjectId('65b...')","amount":6200,"status":"pending","valid_until":"2026-03-05T00:00:00Z"}
```
- Embedding vs referencing: line items embedded; event/vendor referenced.
- Scale: prevents duplicate active quotes.

## bookings
- Fields: `_id`, `event_id:ObjectId`, `user_id:ObjectId`, `vendor_id:ObjectId`, `quote_id:ObjectId|null`, `status:str`, `total_amount:float`, `currency:str`, `booked_at`, `created_at`, `updated_at`
- Indexes: `(event_id,status)`, `(vendor_id,status,created_at desc)`, partial unique `event_id` for active statuses
- Example:
```json
{"event_id":"ObjectId('660...')","vendor_id":"ObjectId('65b...')","status":"confirmed","total_amount":6200}
```
- Embedding vs referencing: header only, milestones and escrow in separate collections.
- Scale: event-level uniqueness and vendor workload queries.

## milestones
- Fields: `_id`, `booking_id:ObjectId`, `sequence:int`, `title:str`, `amount:float`, `status:str`, `due_at:datetime`, `released_at:datetime|null`, `created_at`, `updated_at`
- Indexes: `(booking_id,sequence unique)`, `(booking_id,status)`, `(due_at,status)`
- Example:
```json
{"booking_id":"ObjectId('661...')","sequence":1,"title":"Deposit","amount":1860,"status":"locked","due_at":"2026-03-01T00:00:00Z"}
```
- Embedding vs referencing: separate to support independent lifecycle and locks.
- Scale: high-frequency status updates.

## escrow_transactions
- Fields: `_id`, `booking_id:ObjectId`, `milestone_id:ObjectId|null`, `tx_type:str`, `amount:float`, `currency:str`, `status:str`, `provider_ref:str|null`, `created_at`, `updated_at`, `expires_at:datetime|null`
- Indexes: `(booking_id,milestone_id,tx_type)`, `(status,created_at desc)`, `expires_at TTL sparse`
- Example:
```json
{"booking_id":"ObjectId('661...')","milestone_id":"ObjectId('662...')","tx_type":"lock","amount":1860,"status":"succeeded"}
```
- Embedding vs referencing: immutable ledger rows; no embedding in booking.
- Scale: append-heavy, auditable.

## negotiations
- Fields: `_id`, `event_id:ObjectId`, `vendor_id:ObjectId`, `status:str`, `rounds:[{round,offer,counter,accepted_probability,created_at}]`, `current_offer:float`, `last_activity_at`, `expires_at`
- Indexes: `(event_id,vendor_id,status)`, `(vendor_id,last_activity_at desc)`, `expires_at TTL sparse`
- Example:
```json
{"event_id":"ObjectId('660...')","vendor_id":"ObjectId('65b...')","status":"open","rounds":[{"round":1,"offer":6000,"counter":6150,"accepted_probability":0.71}]}
```
- Embedding vs referencing: rounds embedded per negotiation thread.
- Scale: bounded rounds; TTL for stale threads.

## trust_scores
- Fields: `_id`, `vendor_id:ObjectId`, `score:float`, `signals:{completion_rate,dispute_rate,response_sla,recent_reviews}`, `updated_at`
- Indexes: `vendor_id(unique)`, `(score desc,updated_at desc)`
- Example:
```json
{"vendor_id":"ObjectId('65b...')","score":84.3,"signals":{"completion_rate":0.97,"dispute_rate":0.01},"updated_at":"2026-02-25T08:00:00Z"}
```
- Embedding vs referencing: denormalized aggregate materialization.
- Scale: read-heavy for ranking.

## vendor_analytics
- Fields: `_id`, `vendor_id:ObjectId`, `day:date`, `category:str`, `quote_count:int`, `booking_count:int`, `average_quote:float`, `average_discount_pct:float`, `cancellations:int`
- Indexes: `(vendor_id,day unique)`, `(category,day desc)`
- Example:
```json
{"vendor_id":"ObjectId('65b...')","day":"2026-02-24","quote_count":14,"booking_count":6,"average_quote":5940}
```
- Embedding vs referencing: daily rollup table, no embedding.
- Scale: analytics partitions by day; supports time-window queries.

## decision_scores
- Fields: `_id`, `event_id:ObjectId`, `vendor_id:ObjectId`, `score:int`, `base_decision_score:int`, `risk_adjusted_score:int`, `components:{price_fairness,availability_confidence,trust_score,demand_pressure,negotiation_probability,dispute_risk_score}`, `recommendation:str`, `model_version:int`, `risk_version:int`, `is_canary:bool`, `request_id:str`, `explanation:[str]`, `risks:[str]`, `created_at`, `expires_at`
- Indexes: `(event_id,vendor_id unique)`, `(score desc,created_at desc)`, `(model_version,created_at desc)`, `(risk_version,created_at desc)`, `expires_at TTL sparse`
- Example:
```json
{"event_id":"ObjectId('660...')","vendor_id":"ObjectId('65b...')","score":79,"recommendation":"book_now","components":{"price_fairness":82.1}}
```
- Embedding vs referencing: decision snapshots stored independently for audit/history.
- Scale: short-lived cache with TTL; recompute friendly.

## decision_outcomes
- Fields: `_id`, `decision_id:ObjectId`, `booking_id:ObjectId`, `event_id:ObjectId`, `vendor_id:ObjectId`, `actual_booking_result:bool`, `actual_completion_status:str`, `actual_dispute_flag:bool`, `actual_final_price:float`, `model_version:int`, `predicted_booking_result:bool`, `predicted_dispute_flag:bool`, `predicted_features:{...}`, `accuracy_metrics:{score_error,negotiation_probability_error,trust_score_error,price_fairness_error,...}`, `created_at`
- Indexes: `decision_id(unique,sparse)`, `booking_id(unique)`, `(model_version,created_at desc)`, `(actual_completion_status,actual_dispute_flag)`
- Example:
```json
{"decision_id":"ObjectId('66a...')","booking_id":"ObjectId('66b...')","actual_completion_status":"completed","actual_dispute_flag":false,"actual_final_price":6150,"model_version":3}
```
- Embedding vs referencing: separate outcomes table for post-hoc model evaluation.
- Scale: append-only, optimized for calibration windows.

## decision_outcomes_extended
- Fields: `_id`, `booking_id:ObjectId`, `model_version:int`, `risk_version:int`, `is_canary:bool`, `predicted_score:float`, `actual_outcome:str`, `revenue_impact:float`, `dispute_occurred:bool`, `timestamp`
- Indexes: `(model_version,timestamp desc)`, plus booking/risk/canary timeline indexes
- Example:
```json
{"booking_id":"ObjectId('66b...')","model_version":7,"risk_version":3,"is_canary":false,"predicted_score":78.0,"actual_outcome":"success","revenue_impact":6200.0,"dispute_occurred":false}
```
- Scale: financial-impact feedback stream for profitability safety.

## decision_model_config
- Fields: `_id`, `model_version:int`, `weights:{price_weight,availability_weight,trust_weight,demand_weight,negotiation_weight}`, `performance_metrics:object`, `active_flag:bool`, `frozen:bool`, `created_at`, `last_calibration_date`
- Indexes: `model_version(unique)`, `(active_flag,created_at desc)`, `(created_at desc)`
- Example:
```json
{"model_version":4,"weights":{"price_weight":0.26,"availability_weight":0.23,"trust_weight":0.25,"demand_weight":0.12,"negotiation_weight":0.14},"active_flag":true}
```
- Embedding vs referencing: independent config registry to version model parameters.
- Scale: tiny control-plane collection; read on every scoring path via indexed active flag.

## calibration_audit_logs
- Fields: `_id`, `model_version_from:int`, `model_version_to:int|null`, `previous_accuracy:float`, `new_accuracy:float`, `weight_changes:object`, `aborted_flag:bool`, `reason:str`, `created_at`
- Indexes: `(model_version_from,created_at desc)`, `(aborted_flag,created_at desc)`
- Example:
```json
{"model_version_from":6,"model_version_to":7,"previous_accuracy":0.78,"new_accuracy":0.81,"aborted_flag":false,"reason":"calibration_applied"}
```
- Embedding vs referencing: append-only model lifecycle audit table.
- Scale: low write volume, high diagnostic value.

## calibration_locks
- Fields: `_id:str`, `owner_id:str`, `lease_expires_at:datetime`, `created_at`, `updated_at`
- Indexes: `lease_expires_at TTL`
- Example:
```json
{"_id":"decision_model_calibration","owner_id":"auto:abc123","lease_expires_at":"2026-02-25T13:00:00Z"}
```
- Embedding vs referencing: dedicated mutex document collection.
- Scale: single hot key lock, TTL guarantees stale-lock cleanup.

## booking_risk_snapshots
- Fields: `_id`, `booking_id:str`, `event_id:str`, `vendor_id:ObjectId`, `category:str`, `city:str`, `quoted_price:float`, `trust_score:float`, `negotiation_probability:float`, `signals:{vendor_dispute_ratio,milestone_delay_rate,cancellation_rate,negotiation_aggressiveness,historical_booking_price_deviation}`, `risk_version:int`, `dispute_risk_score:float`, `created_at`
- Indexes: `(booking_id,created_at desc)`, `(vendor_id,created_at desc)`, `(risk_version,created_at desc)`
- Example:
```json
{"booking_id":"663f...","risk_version":1,"dispute_risk_score":42.7}
```
- Embedding vs referencing: snapshot table for per-decision risk traces.
- Scale: append-only, optimized by booking and vendor timelines.

## market_signals
- Fields: `_id`, `category:str`, `city:str`, `booking_volume_7d:int`, `city_surge_index:float`, `seasonal_multiplier:float`, `availability_shrink_rate:float`, `demand_pressure:float`, `created_at`, `expires_at`
- Indexes: `(category,city,created_at desc)`, `expires_at TTL (30d)`
- Example:
```json
{"category":"catering","city":"Austin","demand_pressure":0.73}
```
- Embedding vs referencing: independent short-lived market intelligence docs.
- Scale: periodic aggregate writes with TTL pruning.

## risk_model_config
- Fields: model docs -> `_id:ObjectId`, `risk_version:int`, `weights:object`, `adjustment:{dispute_risk_weight,demand_urgency_weight}`, `active_flag:bool`, `created_at`; control doc -> `_id:'risk_model_control'`, `active_version:int`, `canary_version:int|null`, `canary_traffic_percentage:int`, `shadow_version:int|null`, `updated_at`
- Indexes: `risk_version(unique,sparse)`, `(active_flag,created_at desc)`, control lookup indexes on active/canary fields
- Example:
```json
{"risk_version":1,"adjustment":{"dispute_risk_weight":0.18,"demand_urgency_weight":0.14},"active_flag":true}
```
- Embedding vs referencing: separate risk model lifecycle from decision model lifecycle.
- Scale: low-churn control-plane collection.

## feature_drift_alerts
- Fields: `_id`, `feature_name:str`, `rolling_mean:float`, `baseline_mean:float`, `baseline_std:float`, `z_score:float`, `created_at`
- Indexes: `(feature_name,created_at desc)`, `(created_at desc)`
- Scale: append-only alert feed for drift incidents.

## ai_execution_logs
- Fields: `_id`, `request_id:str`, `model_version:int`, `risk_version:int`, `features_used:object`, `execution_time_ms:float`, `fallback_used:bool`, `timestamp`
- Indexes: `(model_version,timestamp desc)`, `request_id(unique)`
- Scale: high-write observability stream, query by model/time.

## shadow_model_logs
- Fields: `_id`, `request_id:str`, `booking_id:str`, `active_risk_version:int`, `shadow_version:int`, `active_dispute_risk_score:float`, `shadow_dispute_risk_score:float`, `timestamp`
- Indexes: `(shadow_version,timestamp desc)`, `request_id`
- Scale: shadow experimentation telemetry.

## ai_profit_alerts
- Fields: `_id`, `last_7d_revenue:float`, `last_7d_dispute_cost:float`, `net_profit_delta_vs_baseline:float`, `canary_vs_active_profit_gap:float`, `alert_type:str`, `freeze_triggered:bool`, `timestamp`
- Indexes: `(alert_type,timestamp desc)`, `(timestamp desc)`
- Scale: low-volume guardrail alerts.

## ai_rollback_logs
- Fields: `_id`, `model_type:str`, `target_version:int`, `actor:str`, `timestamp`
- Indexes: `(model_type,timestamp desc)`
- Scale: audit of admin rollback operations.

## risk_weight_audit_logs
- Fields: `_id`, `from_risk_version:int`, `to_risk_version:int`, `dispute_rate:float`, `booking_accuracy_previous:float`, `booking_accuracy_current:float`, `accuracy_drop:float`, `weight_changes:object`, `reason:str`, `created_at`
- Indexes: `(from_risk_version,created_at desc)`, `(to_risk_version,created_at desc)`
- Scale: low-write governance history.

## ai_control_config
- Fields: `_id:'global'`, `freeze_all_models:bool`, `freeze_risk_model:bool`, `freeze_decision_model:bool`, `created_at`, `updated_at`
- Indexes: `(updated_at desc)`
- Scale: singleton global controls.

## ai_financial_control
- Fields: `_id:'global'`, `max_daily_risk_exposure:float`, `max_dispute_rate:float`, `auto_freeze_enabled:bool`, `created_at`, `updated_at`
- Indexes: `(updated_at desc)`
- Scale: singleton financial safety thresholds for runtime scoring gates.
