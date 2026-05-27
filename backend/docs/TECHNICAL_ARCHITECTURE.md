# Backend Technical Documentation

## 1. Refactored Architecture

### Runtime Entrypoint
- Canonical runtime: `backend/main.py`
- Compatibility wrappers (non-initializing): `backend/server.py`, `backend/app/main.py`

### Refactored Backend Structure
```text
backend/
  main.py
  core/
  routers/
  services/
    ai_booking_service.py
  payments/
    execution_service.py
  ai_core/
  models/
  workers/
  docs/
    TECHNICAL_ARCHITECTURE.md
```

### System Architecture Diagram
```mermaid
flowchart LR
    Client[Web/Mobile Client] --> API[FastAPI backend/main.py]
    API --> Auth[Auth + RBAC]
    API --> Assist[AI Booking Service]
    API --> Pay[Payment Execution Service]
    API --> WS[WebSocket Notifications]
    API --> DB[(MongoDB)]
    Pay --> Razorpay[Razorpay Orders/Webhooks/Payouts]
    DB --> Metrics[Prometheus Metrics]
```

## 2. Use Case Diagram
```mermaid
flowchart TB
    U[Customer] --> UC1[Create booking intent]
    U --> UC2[Pay with Razorpay]
    U --> UC3[Use AI booking assistant]
    V[Vendor] --> UC4[Manage bookings]
    V --> UC5[Receive payouts]
    A[Admin] --> UC6[Approve/Reject payouts]
    R[Razorpay] --> UC7[Send payment.captured webhook]
```

## 3. Payment Sequence Diagram
```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant RZP as Razorpay
    participant DB as MongoDB

    C->>API: POST /api/bookings/{intent_id}/pay
    API->>RZP: Create order
    API->>DB: Save payment CREATED

    RZP->>API: webhook payment.captured + signature + event_id
    API->>API: Verify signature and event type
    API->>DB: Insert webhook_events(event_id) [unique]
    API->>DB: Txn: payment CONFIRMED + materialize booking

    Note over API,DB: Booking completion path
    C->>API: POST /api/bookings/{id}/action (complete)
    API->>RZP: Create payout transfer
    RZP-->>API: payout processed
    API->>DB: Txn: payout PROCESSED
    API->>DB: Update booking COMPLETED
```

## 4. API Documentation (Core)
- `GET /health`:
  - `status`
  - `timestamp`
  - `database_connection`
- `GET /metrics` (Prometheus format)
- `POST /api/bookings/webhook`:
  - required headers: `x-razorpay-signature`, `x-razorpay-event-id`
  - accepts only `payment.captured`
- `POST /api/bookings/verify`
- `POST /api/admin/payouts/{payout_id}/action`:
  - approve requires `x-idempotency-key`
- `POST /api/assistant/booking/route`

## 5. SDLC Stages Used
1. Discovery and architecture audit
2. Risk modeling (payments, auth, secrets)
3. Incremental refactor and module extraction
4. Defensive coding (idempotency, replay protection, transactions)
5. Observability and operations hardening
6. Deployment artifact update and documentation

## 6. Deployment Architecture
```mermaid
flowchart TB
    LB[Ingress/Load Balancer] --> API1[FastAPI Container]
    API1 --> M[(MongoDB Replica Set)]
    API1 --> RZP[Razorpay API]
    API1 --> PM[Prometheus Scrape /metrics]
```

## 7. Environment and Secret Hygiene
- Remove tracked secrets from repository (`backend/.env` removed)
- Keep only templates (`.env.example`)
- Rotate keys:
  - `JWT_SECRET_KEY`
  - `RAZORPAY_KEY_SECRET`
  - `RAZORPAY_WEBHOOK_SECRET`
- Provide runtime secrets via container/runtime secret store.

## 8. Monitoring Signals
- `webhook_events_total{event,outcome}`
- `payment_processing_latency_seconds{flow}`
- `auth_failures_total{reason,endpoint}`
