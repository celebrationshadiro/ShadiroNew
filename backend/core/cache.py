from __future__ import annotations

import logging
from typing import Any, Optional
import redis.asyncio as redis
from core.config import get_settings

try:
    import orjson
    _HAS_ORJSON = True
except ImportError:
    import json as orjson
    _HAS_ORJSON = False

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis Caching Service for high-scale API response caching.
    Implements S6 connection pooling and orjson high-performance serialization.
    """

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None

    async def connect(self) -> None:
        if self.redis is not None:
            return
        # S6 connection pool settings
        pool = redis.ConnectionPool.from_url(
            self.redis_url,
            max_connections=20,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True
        )
        self.redis = redis.Redis(connection_pool=pool)
        await self.redis.ping()
        logger.info("CacheService connected to Redis successfully with pool size 20.")

    async def close(self) -> None:
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("CacheService connection closed.")

    async def get(self, key: str) -> Optional[dict | list]:
        if not self.redis:
            await self.connect()
        try:
            val = await self.redis.get(key)
            if val is None:
                return None
            
            # Serialize/deserialize with orjson for speed
            if _HAS_ORJSON:
                return orjson.loads(val)
            else:
                import json
                # Handle bytes decoding safely
                decoded = val.decode("utf-8") if isinstance(val, bytes) else val
                return json.loads(decoded)
        except Exception as e:
            logger.error(f"CacheService get error for key={key}: {e}")
            return None

    async def set(self, key: str, value: dict | list, ttl: int) -> None:
        if not self.redis:
            await self.connect()
        try:
            if _HAS_ORJSON:
                serialized = orjson.dumps(value)
            else:
                import json
                serialized = json.dumps(value)
            await self.redis.set(key, serialized, ex=ttl)
        except Exception as e:
            logger.error(f"CacheService set error for key={key}: {e}")

    async def delete(self, key: str) -> None:
        if not self.redis:
            await self.connect()
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"CacheService delete error for key={key}: {e}")

    async def delete_pattern(self, pattern: str) -> None:
        if not self.redis:
            await self.connect()
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"CacheService delete_pattern error for pattern={pattern}: {e}")


_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    global _cache_service
    if _cache_service is None:
        settings = get_settings()
        _cache_service = CacheService(settings.REDIS_URL)
    return _cache_service
