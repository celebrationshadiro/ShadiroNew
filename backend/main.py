from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from core.config import get_settings
from core.rate_limiting import RedisRateLimitMiddleware, ShadiroRateLimitMiddleware
from core.middleware import RequestContextLoggingMiddleware
from core.prometheus import PrometheusMetricsMiddleware, metrics_response
from core.response_envelope import EnvelopeResponseMiddleware
from core.security import check_jwt_config, decode_access_token, get_rate_limiter
from core.startup import shutdown_resources, startup_resources
from core.websocket_broker import RedisWebSocketBroker
from middleware.security import configure_security_middleware
from app.api.v1.routes import api_router

try:
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    from slowapi import _rate_limit_exceeded_handler

    _HAS_SLOWAPI = True
except Exception:
    _HAS_SLOWAPI = False

settings = get_settings()

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastAPIIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration
    _HAS_SENTRY = True
except ImportError:
    _HAS_SENTRY = False

if _HAS_SENTRY and settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastAPIIntegration(transaction_style="endpoint"),
        ],
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging as _logging
    _log = _logging.getLogger("core.startup")

    check_jwt_config()
    await startup_resources(app, settings)
    
    # --- Redis WebSocket Broker (graceful) ---
    broker = None
    try:
        broker = RedisWebSocketBroker(settings.REDIS_URL)
        await broker.connect_redis()
        app.state.websocket_broker = broker
    except Exception as exc:
        _log.warning("Redis unavailable – WebSocket broker disabled for this session: %s", exc)
        app.state.websocket_broker = None
        broker = None

    # --- Redis Cache (graceful) ---
    cache = None
    try:
        from core.cache import get_cache_service
        cache = get_cache_service()
        await cache.connect()
        app.state.cache = cache
    except Exception as exc:
        _log.warning("Redis unavailable – Cache service disabled for this session: %s", exc)
        app.state.cache = None
        cache = None
    
    try:
        yield
    finally:
        if cache:
            await cache.close()
        if broker:
            await broker.disconnect_redis()
        await shutdown_resources(app)


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Production API for Shadiro marketplace, bookings, payments, vendors, and event planning.",
    contact={"name": "Shadiro Engineering", "url": "https://shadiro.com"},
    servers=[
        {"url": "https://api.shadiro.com", "description": "Production"},
        {"url": "http://localhost:8000", "description": "Local development"},
    ],
    lifespan=lifespan,
)
app.state.limiter = get_rate_limiter()
app.add_middleware(RequestContextLoggingMiddleware)
app.add_middleware(PrometheusMetricsMiddleware)
app.add_middleware(EnvelopeResponseMiddleware)
app.add_middleware(ShadiroRateLimitMiddleware)
configure_security_middleware(app, settings)
if _HAS_SLOWAPI:
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # tighten in prod


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    if not response.headers.get("Strict-Transport-Security"):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.include_router(api_router)


def _validate_ws_identity(token_user_id: str, path_user_id: str) -> None:
    if str(token_user_id or "") != str(path_user_id or ""):
        raise HTTPException(status_code=403, detail="User mismatch")


@app.websocket("/ws/notifications/{user_id}")
async def notifications_ws(websocket: WebSocket, user_id: str):
    broker = getattr(websocket.app.state, "websocket_broker", None)
    await websocket.accept()
    if not broker:
        await websocket.send_json({"type": "error", "detail": "websocket_broker_unavailable"})
        await websocket.close(code=1011)
        return

    forward_task = None
    try:
        auth_message = await websocket.receive_json()
        if auth_message.get("type") != "auth" or not auth_message.get("token"):
            await websocket.close(code=1008, reason="Missing auth token")
            return
        payload = decode_access_token(auth_message["token"])
        _validate_ws_identity(str(payload.get("sub")), user_id)
        
        await broker.connect(user_id, websocket)
        await websocket.send_json({"type": "connected", "user_id": user_id})
        
        # Start background forwarding task for notifications
        forward_task = asyncio.create_task(
            broker.subscribe_and_forward(user_id, websocket, "ws:notifications")
        )
        
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        return
    except Exception:
        with suppress(Exception):
            await websocket.close(code=1011, reason="WebSocket server error")
    finally:
        if forward_task:
            forward_task.cancel()
            with suppress(asyncio.CancelledError):
                await forward_task
        await broker.disconnect(user_id, websocket)


@app.websocket("/ws/delivery/{user_id}")
async def delivery_ws(websocket: WebSocket, user_id: str):
    """
    Authenticated delivery channel: user-scoped events + optional job subscriptions.
    Client sends {"type":"auth","token":"..."} first, then {"type":"sub_job","job_id":"..."}.
    """
    broker = getattr(websocket.app.state, "websocket_broker", None)
    await websocket.accept()
    if not broker:
        await websocket.send_json({"type": "error", "detail": "websocket_broker_unavailable"})
        await websocket.close(code=1011)
        return

    forward_task = None
    job_tasks: dict[str, asyncio.Task] = {}
    try:
        auth_message = await websocket.receive_json()
        if auth_message.get("type") != "auth" or not auth_message.get("token"):
            await websocket.close(code=1008, reason="Missing auth token")
            return
        payload = decode_access_token(auth_message["token"])
        _validate_ws_identity(str(payload.get("sub")), user_id)
        
        await broker.connect(user_id, websocket)
        await websocket.send_json({"type": "delivery_connected", "user_id": user_id})
        
        # Start background forwarding task for user delivery notifications
        forward_task = asyncio.create_task(
            broker.subscribe_and_forward(user_id, websocket, "ws:delivery")
        )
        
        while True:
            msg = await websocket.receive_json()
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            if msg.get("type") == "sub_job" and msg.get("job_id"):
                jid = str(msg["job_id"])
                if jid not in job_tasks:
                    job_tasks[jid] = asyncio.create_task(
                        broker.subscribe_and_forward(jid, websocket, "ws:delivery:job")
                    )
                    await websocket.send_json({"type": "subscribed", "job_id": jid})
            if msg.get("type") == "unsub_job" and msg.get("job_id"):
                jid = str(msg["job_id"])
                if jid in job_tasks:
                    job_tasks[jid].cancel()
                    with suppress(asyncio.CancelledError):
                        await job_tasks[jid]
                    del job_tasks[jid]
                    await websocket.send_json({"type": "unsubscribed", "job_id": jid})
    except WebSocketDisconnect:
        pass
    except Exception:
        with suppress(Exception):
            await websocket.close(code=1011, reason="WebSocket server error")
    finally:
        if forward_task:
            forward_task.cancel()
            with suppress(asyncio.CancelledError):
                await forward_task
        for task in job_tasks.values():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        await broker.disconnect(user_id, websocket)


@app.get("/health", tags=["infrastructure"])
async def health_liveness():
    return {
        "status": "alive",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health/ready", tags=["infrastructure"])
@app.get("/ready", tags=["infrastructure"])
async def health_readiness():
    checks = {}
    ready = True
    
    # 1. MongoDB Check
    db = getattr(app.state, "db", None)
    if db is None:
        checks["mongodb"] = "error"
        ready = False
    else:
        try:
            await db.command("ping")
            checks["mongodb"] = "ok"
        except Exception:
            checks["mongodb"] = "error"
            ready = False

    # 2. Redis Client Check
    redis_client = getattr(app.state, "redis", None)
    if redis_client is None:
        checks["redis"] = "error"
        ready = False
    else:
        try:
            await redis_client.ping()
            checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "error"
            ready = False

    # 3. WebSocket Broker Check
    broker = getattr(app.state, "websocket_broker", None)
    if broker is None or broker.redis is None:
        checks["websocket_broker"] = "error"
        ready = False
    else:
        try:
            await broker.redis.ping()
            checks["websocket_broker"] = "ok"
        except Exception:
            checks["websocket_broker"] = "error"
            ready = False

    # 4. Cache Check
    cache = getattr(app.state, "cache", None)
    if cache is None or cache.redis is None:
        checks["cache"] = "error"
        ready = False
    else:
        try:
            await cache.redis.ping()
            checks["cache"] = "ok"
        except Exception:
            checks["cache"] = "error"
            ready = False

    status_code = 200 if ready else 503
    return JSONResponse(
        status_code=status_code,
        content={"ready": ready, "checks": checks}
    )


@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics():
    return metrics_response()
