# API Documentation Summary

## Auth
- AI endpoints require JWT user auth and `X-API-Key`.
- AI endpoints are rate-limited per client IP.

## Decision
- `POST /api/v1/decision/book-now-score`
  - Computes decision, risk-adjusted score, canary/shadow-aware metadata.
- `GET /api/v1/decision/model/performance`
  - Returns decision model performance and stability metrics.
- `POST /api/v1/decision/model/calibrate`
  - Admin-only manual calibration.

## AI Control
- `GET /api/v1/ai/drift/status`
  - Returns current drift signals and recent drift alerts.
- `GET /api/v1/ai/health`
  - Returns model health + profitability telemetry.
- `POST /api/v1/ai/rollback`
  - Admin-only model rollback (`risk`/`decision`).

## Market
- `GET /api/v1/market/price/forecast?category=...&city=...`
  - Returns 7/30 day predicted market price movement.

## Ops
- `GET /healthz` liveness
- `GET /readyz` readiness (DB ping)

