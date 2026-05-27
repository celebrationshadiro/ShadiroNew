# AI Core Module

## Overview
`ai_core` is a standalone module that encapsulates all AI decision/risk/drift/profit logic for deployment as an isolated service layer.

## Structure
- `config.py`: centralized `AIConfig` environment loader.
- `control_plane.py`: API key auth, route guard, rate limiting, rollback logs.
- `model_registry.py`: model calibration/performance/rollback orchestration.
- `decision_engine.py`: decision scoring and websocket publication integration.
- `risk_engine.py`: risk engine control paths.
- `drift_monitor.py`: feature drift access.
- `profit_monitor.py`: AI health + profitability aggregation.
- `module.py`: dependency-bound module assembly.

## Architecture Diagram
See [ARCHITECTURE.md](c:\Users\suman\Downloads\app-main\Event-app-main\backend\ai_core\ARCHITECTURE.md).

## API Summary
See [API_SUMMARY.md](c:\Users\suman\Downloads\app-main\Event-app-main\backend\ai_core\API_SUMMARY.md).

## Deploy
```bash
cd backend/ai_core
docker compose up --build
```

## Endpoints
- `GET /healthz`
- `GET /readyz`
- `POST /api/v1/decision/book-now-score`
- `GET /api/v1/decision/model/performance`
- `POST /api/v1/decision/model/calibrate`
- `GET /api/v1/ai/drift/status`
- `GET /api/v1/ai/health`
- `POST /api/v1/ai/rollback`
- `GET /api/v1/market/price/forecast`

