from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from typing import Any

from fastapi import FastAPI

from core.config import Settings
from core.database import build_mongo_manager
from core.logging import configure_logging
from core.rate_limiting import SlidingWindowLimiter
from integrations.razorpay_client import build_razorpay_client
from services.automation_engine import run_automation_worker
from shadiro_delivery_network.realtime_hub import DeliveryRealtimeHub
from workers.sla_worker import run_sla_worker

try:
    import redis.asyncio as redis_async

    _HAS_REDIS = True
except Exception:  # pragma: no cover
    redis_async = None
    _HAS_REDIS = False

logger = logging.getLogger(__name__)


async def _connect_redis(settings: Settings) -> Any | None:
    if not settings.REDIS_URL:
        logger.warning("redis_not_configured", extra={"event": "redis_not_configured"})
        return None
    if not _HAS_REDIS:
        logger.warning("redis_dependency_missing", extra={"event": "redis_dependency_missing"})
        return None

    client = redis_async.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=False,
        socket_connect_timeout=2,
        socket_timeout=2,
        health_check_interval=30,
    )
    try:
        await client.ping()
        logger.info("redis_connected", extra={"event": "redis_connected"})
        return client
    except Exception:
        logger.exception("redis_connect_failed", extra={"event": "redis_connect_failed"})
        with suppress(Exception):
            await client.aclose()
        return None


async def startup_resources(app: FastAPI, settings: Settings) -> None:
    configure_logging(settings.LOG_LEVEL)

    mongo = build_mongo_manager(settings)
    await mongo.connect()
    await mongo.ensure_indexes()

    redis_client = await _connect_redis(settings)

    app.state.mongo = mongo
    app.state.mongo_manager = mongo
    app.state.db = mongo.db
    app.state.redis = redis_client
    app.state.sliding_rate_limiter = SlidingWindowLimiter(redis_client)
    app.state.settings = settings
    app.state.razorpay_client = build_razorpay_client(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    app.state.delivery_hub = DeliveryRealtimeHub()

    app.state.automation_task = asyncio.create_task(run_automation_worker(mongo.db))
    app.state.sla_worker_task = asyncio.create_task(run_sla_worker())
    logger.info("startup_complete", extra={"event": "startup_complete"})


async def shutdown_resources(app: FastAPI) -> None:
    for task_name in ("automation_task", "sla_worker_task"):
        task = getattr(app.state, task_name, None)
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    redis_client = getattr(app.state, "redis", None)
    if redis_client is not None:
        with suppress(Exception):
            await redis_client.aclose()

    mongo = getattr(app.state, "mongo_manager", None) or getattr(app.state, "mongo", None)
    if mongo:
        await mongo.close()

    logger.info("shutdown_complete", extra={"event": "shutdown_complete"})
