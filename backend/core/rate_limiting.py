"""
Consolidated rate-limiting module for the Shadiro platform.

Merged from:
  - core/rate_limit.py   → SlidingWindowLimiter, RateLimitRule, RateLimitDecision,
                            RedisRateLimitMiddleware (generic auth/public split)
  - core/rate_limiter.py → ShadiroRateLimitMiddleware (tiered per-endpoint limits),
                            ENDPOINT_LIMITS
"""
from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Deque, Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import Settings, get_settings

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Data classes  (from rate_limit.py)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class RateLimitRule:
    name: str
    limit: int
    window_seconds: int
    burst_limit: int
    burst_window_seconds: int


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after_seconds: int
    rule_name: str


# ──────────────────────────────────────────────────────────────────────────────
# Sliding-window limiter engine  (from rate_limit.py — Lua + in-memory fallback)
# ──────────────────────────────────────────────────────────────────────────────

class SlidingWindowLimiter:
    """Redis-backed sliding window limiter with an in-memory development fallback."""

    _LUA_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]
redis.call('ZREMRANGEBYSCORE', key, 0, now - window_ms)
local count = redis.call('ZCARD', key)
if count >= limit then
  local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
  local retry_after = 1
  if oldest[2] then
    retry_after = math.ceil(((tonumber(oldest[2]) + window_ms) - now) / 1000)
    if retry_after < 1 then retry_after = 1 end
  end
  return {0, 0, retry_after}
end
redis.call('ZADD', key, now, member)
redis.call('PEXPIRE', key, window_ms)
return {1, limit - count - 1, 0}
"""

    def __init__(self, redis_client: Optional[Any] = None, *, prefix: str = "shadiro:rl"):
        self.redis = redis_client
        self.prefix = prefix
        self._memory: dict[str, Deque[float]] = defaultdict(deque)

    async def check(self, *, identity: str, rule: RateLimitRule) -> RateLimitDecision:
        normal = await self._check_window(
            key=f"{self.prefix}:{rule.name}:{identity}",
            limit=rule.limit,
            window_seconds=rule.window_seconds,
        )
        if not normal.allowed:
            return RateLimitDecision(False, normal.remaining, normal.retry_after_seconds, rule.name)

        burst = await self._check_window(
            key=f"{self.prefix}:{rule.name}:burst:{identity}",
            limit=rule.burst_limit,
            window_seconds=rule.burst_window_seconds,
        )
        if not burst.allowed:
            return RateLimitDecision(False, burst.remaining, burst.retry_after_seconds, f"{rule.name}_burst")

        return RateLimitDecision(True, min(normal.remaining, burst.remaining), 0, rule.name)

    async def _check_window(self, *, key: str, limit: int, window_seconds: int) -> RateLimitDecision:
        if self.redis is None:
            return self._check_memory(key=key, limit=limit, window_seconds=window_seconds)

        now_ms = int(time.time() * 1000)
        member = f"{now_ms}:{uuid.uuid4().hex}"
        try:
            allowed, remaining, retry_after = await self.redis.eval(
                self._LUA_SCRIPT,
                1,
                key,
                now_ms,
                window_seconds * 1000,
                limit,
                member,
            )
            return RateLimitDecision(bool(int(allowed)), int(remaining), int(retry_after), key)
        except Exception:
            logger.exception("redis_rate_limit_failed", extra={"event": "redis_rate_limit_failed"})
            return self._check_memory(key=key, limit=limit, window_seconds=window_seconds)

    def _check_memory(self, *, key: str, limit: int, window_seconds: int) -> RateLimitDecision:
        now = time.monotonic()
        cutoff = now - window_seconds
        bucket = self._memory[key]
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            retry_after = max(1, int(bucket[0] + window_seconds - now))
            return RateLimitDecision(False, 0, retry_after, key)
        bucket.append(now)
        return RateLimitDecision(True, max(0, limit - len(bucket)), 0, key)


# ──────────────────────────────────────────────────────────────────────────────
# Generic auth/public rate-limit middleware  (from rate_limit.py)
# ──────────────────────────────────────────────────────────────────────────────

class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """Broad auth vs public rate-limit split using SlidingWindowLimiter."""

    EXEMPT_PREFIXES = (
        "/health",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    )
    AUTH_PREFIXES = (
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/refresh",
        "/api/auth/forgot-password",
        "/api/auth/reset-password",
        "/api/vendor-register",
    )

    def __init__(self, app, *, settings: Settings):
        super().__init__(app)
        self.settings = settings
        self.auth_rule = RateLimitRule(
            name="auth",
            limit=settings.RATE_LIMIT_AUTH_PER_MINUTE,
            window_seconds=60,
            burst_limit=settings.RATE_LIMIT_AUTH_BURST,
            burst_window_seconds=settings.RATE_LIMIT_BURST_WINDOW_SECONDS,
        )
        self.public_rule = RateLimitRule(
            name="public",
            limit=settings.RATE_LIMIT_PUBLIC_PER_MINUTE,
            window_seconds=60,
            burst_limit=settings.RATE_LIMIT_PUBLIC_BURST,
            burst_window_seconds=settings.RATE_LIMIT_BURST_WINDOW_SECONDS,
        )

    async def dispatch(self, request: Request, call_next):
        if not self.settings.RATE_LIMIT_ENABLED or request.method.upper() == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        if not path.startswith("/api") or path.startswith(self.EXEMPT_PREFIXES):
            return await call_next(request)

        limiter = getattr(request.app.state, "sliding_rate_limiter", None)
        if limiter is None:
            limiter = SlidingWindowLimiter(getattr(request.app.state, "redis", None))
            request.app.state.sliding_rate_limiter = limiter

        rule = self.auth_rule if path.startswith(self.AUTH_PREFIXES) else self.public_rule
        identity = f"{rule.name}:{self._client_ip(request)}"
        decision = await limiter.check(identity=identity, rule=rule)
        if decision.allowed:
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(rule.limit)
            response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
            response.headers["X-RateLimit-Policy"] = rule.name
            return response

        request_id = getattr(request.state, "request_id", "")
        logger.warning(
            "security_event",
            extra={
                "event": "rate_limit_exceeded",
                "path": path,
                "rule": decision.rule_name,
                "request_id": request_id,
            },
        )
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "data": {"retry_after_seconds": decision.retry_after_seconds},
                "message": "Rate limit exceeded",
                "error_code": "RATE_LIMITED",
                "request_id": request_id,
            },
            headers={
                "Retry-After": str(decision.retry_after_seconds),
                "X-RateLimit-Limit": str(rule.limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Policy": rule.name,
            },
        )

    @staticmethod
    def _client_ip(request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",", 1)[0].strip()
        return request.client.host if request.client else "unknown"


# ──────────────────────────────────────────────────────────────────────────────
# Tiered per-endpoint rate-limit middleware  (from rate_limiter.py)
# ──────────────────────────────────────────────────────────────────────────────

# Per-endpoint (limit, window_seconds) tuples
ENDPOINT_LIMITS = {
    # Public endpoints
    "public_vendors": (100, 60),       # 100 req/minute

    # Authenticated customer
    "customer_quotes": (10, 3600),     # 10 req/hour
    "customer_intent": (20, 3600),     # 20 req/hour
    "customer_vendors": (300, 60),     # 300 req/minute

    # Authenticated vendor
    "vendor_respond": (50, 3600),      # 50 req/hour
    "vendor_status": (100, 3600),      # 100 req/hour
    "vendor_get": (500, 60),           # 500 req/minute

    # Webhooks
    "webhook_bookings": (200, 60),     # 200 req/minute
    "webhook_grocery": (200, 60),      # 200 req/minute
}


class ShadiroRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Tiered Redis sliding-window rate-limiting middleware.
    Differentiates public, customer, vendor, and webhook rate limits dynamically.
    """

    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()

    async def dispatch(self, request: Request, call_next):
        if not self.settings.RATE_LIMIT_ENABLED or request.method.upper() == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        method = request.method.upper()

        if not path.startswith("/api"):
            return await call_next(request)

        # 1. Identify webhook endpoints
        if method == "POST" and path == "/api/bookings/webhook":
            allowed, retry_after = await self._is_allowed("webhook_bookings", self._client_ip(request))
            if not allowed:
                return self._rate_limit_response(retry_after)
            return await call_next(request)

        if method == "POST" and path.startswith("/api/grocery/webhook/"):
            allowed, retry_after = await self._is_allowed("webhook_grocery", self._client_ip(request))
            if not allowed:
                return self._rate_limit_response(retry_after)
            return await call_next(request)

        # 2. Extract JWT user token if present to identify authenticated vs public
        user_id = None
        user_role = None
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
            try:
                from core.security import decode_access_token
                payload = decode_access_token(token)
                user_id = str(payload.get("sub"))
                user_role = str(payload.get("role", "")).lower()
            except Exception:
                pass

        # 3. Apply tiered limits based on identity and role
        allowed, retry_after = True, 0
        if user_id:
            if user_role == "vendor":
                if method == "PUT" and path.startswith("/api/quotes/") and path.endswith("/respond"):
                    allowed, retry_after = await self._is_allowed("vendor_respond", user_id)
                elif method == "PATCH" and path.startswith("/api/grocery/vendor/") and path.endswith("/status"):
                    allowed, retry_after = await self._is_allowed("vendor_status", user_id)
                elif method == "GET":
                    allowed, retry_after = await self._is_allowed("vendor_get", user_id)
            else:
                if method == "POST" and path == "/api/quotes":
                    allowed, retry_after = await self._is_allowed("customer_quotes", user_id)
                elif method == "POST" and path.startswith("/api/bookings/") and path.endswith("/intent"):
                    allowed, retry_after = await self._is_allowed("customer_intent", user_id)
                elif path.startswith("/api/vendors"):
                    allowed, retry_after = await self._is_allowed("customer_vendors", user_id)
        else:
            if path.startswith("/api/vendors"):
                allowed, retry_after = await self._is_allowed("public_vendors", self._client_ip(request))

        if not allowed:
            return self._rate_limit_response(retry_after)

        return await call_next(request)

    async def _is_allowed(self, rule_name: str, identity: str) -> tuple[bool, int]:
        limit, window = ENDPOINT_LIMITS[rule_name]
        try:
            from core.cache import get_cache_service
            cache = get_cache_service()
            if not cache.redis:
                await cache.connect()

            key = f"rate_limit:{rule_name}:{identity}"
            now = time.time()
            cutoff = now - window

            async with cache.redis.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(key, 0, cutoff)
                pipe.zcard(key)
                pipe.zadd(key, {f"{now}:{identity}": now})
                pipe.expire(key, window)
                res = await pipe.execute()

            count = res[1]
            if count >= limit:
                oldest = await cache.redis.zrange(key, 0, 0, withscores=True)
                retry_after = 60
                if oldest:
                    oldest_time = oldest[0][1]
                    retry_after = max(1, int(oldest_time + window - now))
                return False, retry_after
            return True, 0
        except Exception as e:
            logger.error(f"Rate limiting failure for rule={rule_name}, identity={identity}: {e}")
            return True, 0

    def _rate_limit_response(self, retry_after: int) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Too many requests",
                "retry_after": retry_after
            },
            headers={
                "Retry-After": str(retry_after)
            }
        )

    @staticmethod
    def _client_ip(request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",", 1)[0].strip()
        return request.client.host if request.client else "unknown"
