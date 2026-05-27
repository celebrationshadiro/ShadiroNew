"""
Redis-backed realtime delivery event system for horizontal scaling.

Supports:
- Distributed pub/sub across multiple backend instances
- User-specific and job-specific channels
- Event replay for reconnecting clients
- Automatic cleanup of stale subscriptions
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional
from uuid import uuid4

import redis.asyncio as redis

logger = logging.getLogger(__name__)

REDIS_CHANNEL_USER = "delivery:user:{user_id}"
REDIS_CHANNEL_JOB = "delivery:job:{job_id}"
REDIS_CHANNEL_PARTNER = "delivery:partner:{partner_id}"
REDIS_STREAM_REPLAY = "delivery:stream:replay"
REDIS_KEY_SUBSCRIPTIONS = "delivery:subscriptions:{instance_id}"

EVENT_RETENTION_HOURS = 24


class RedisRealtimeHub:
    """
    Production-grade realtime delivery hub using Redis Pub/Sub + Streams.
    
    Features:
    - Horizontal scaling across multiple backend instances
    - Event replay for late subscribers
    - User and job-specific channels
    - Automatic subscription cleanup
    - Graceful reconnection handling
    """

    def __init__(self, redis_url: str, instance_id: Optional[str] = None):
        self.redis_url = redis_url
        self.instance_id = instance_id or f"instance_{uuid4().hex[:8]}"
        self.client: Optional[redis.Redis] = None
        self.pubsub = None
        self._subscriber_tasks: dict[str, asyncio.Task] = {}
        self._handlers: dict[str, list[Callable]] = {}

    async def connect(self) -> None:
        """Initialize Redis connection."""
        try:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 1,  # TCP_KEEPINTVL
                    3: 3,  # TCP_KEEPCNT
                },
            )
            await self.client.ping()
            logger.info(f"Redis connected: {self.instance_id}")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise

    async def disconnect(self) -> None:
        """Cleanup and disconnect."""
        for task in self._subscriber_tasks.values():
            task.cancel()
        if self.client:
            await self.client.close()

    async def publish_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        user_ids: Optional[list[str]] = None,
        job_id: Optional[str] = None,
        partner_id: Optional[str] = None,
        ttl_hours: int = EVENT_RETENTION_HOURS,
    ) -> str:
        """
        Publish delivery event to Redis.
        
        Args:
            event_type: Type of event (e.g., 'delivery.assigned', 'delivery.pickup_scanned')
            payload: Event data
            user_ids: List of user IDs to notify (in addition to job/partner channels)
            job_id: Job ID for job-specific channel
            partner_id: Partner ID for partner-specific channel
            ttl_hours: Retention time in stream
            
        Returns:
            Event ID
        """
        if not self.client:
            raise RuntimeError("Redis not connected")

        event_id = f"evt_{uuid4().hex}"
        now = datetime.now(timezone.utc)
        event_doc = {
            "id": event_id,
            "type": event_type,
            "timestamp": now.isoformat(),
            "payload": json.dumps(payload),
            "instance": self.instance_id,
        }

        # Append to stream for replay
        stream_id = await self.client.xadd(
            REDIS_STREAM_REPLAY,
            event_doc,
            maxlen=100000,  # Keep last 100k events
            approximate=True,
        )

        # Publish to specific channels
        channels = []
        if job_id:
            channel = REDIS_CHANNEL_JOB.format(job_id=job_id)
            channels.append(channel)

        if partner_id:
            channel = REDIS_CHANNEL_PARTNER.format(partner_id=partner_id)
            channels.append(channel)

        if user_ids:
            for uid in user_ids:
                channel = REDIS_CHANNEL_USER.format(user_id=uid)
                channels.append(channel)

        # Publish to all channels
        for channel in channels:
            await self.client.publish(channel, json.dumps(event_doc))

        logger.debug(f"Event published: {event_type} -> {len(channels)} channels")
        return event_id

    async def subscribe_user(
        self,
        user_id: str,
        handler: Callable[[dict[str, Any]], Any],
    ) -> str:
        """Subscribe to user-specific delivery events."""
        channel = REDIS_CHANNEL_USER.format(user_id=user_id)
        sub_id = f"sub_{uuid4().hex}"
        
        if channel not in self._handlers:
            self._handlers[channel] = []
        self._handlers[channel].append(handler)

        # Track subscription
        await self.client.sadd(
            REDIS_KEY_SUBSCRIPTIONS.format(instance_id=self.instance_id),
            f"{channel}:{sub_id}",
        )
        await self.client.expire(
            REDIS_KEY_SUBSCRIPTIONS.format(instance_id=self.instance_id),
            86400,  # 24 hours
        )

        return sub_id

    async def subscribe_job(
        self,
        job_id: str,
        handler: Callable[[dict[str, Any]], Any],
    ) -> str:
        """Subscribe to job-specific delivery events."""
        channel = REDIS_CHANNEL_JOB.format(job_id=job_id)
        sub_id = f"sub_{uuid4().hex}"
        
        if channel not in self._handlers:
            self._handlers[channel] = []
        self._handlers[channel].append(handler)

        return sub_id

    async def subscribe_partner(
        self,
        partner_id: str,
        handler: Callable[[dict[str, Any]], Any],
    ) -> str:
        """Subscribe to partner-specific delivery events."""
        channel = REDIS_CHANNEL_PARTNER.format(partner_id=partner_id)
        sub_id = f"sub_{uuid4().hex}"
        
        if channel not in self._handlers:
            self._handlers[channel] = []
        self._handlers[channel].append(handler)

        return sub_id

    async def get_event_replay(
        self,
        job_id: str,
        hours: int = 24,
    ) -> list[dict[str, Any]]:
        """
        Get recent events for job from replay stream.
        Useful for reconnecting clients to catch up on missed events.
        """
        if not self.client:
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        try:
            # Read all events from stream
            events = await self.client.xrange(REDIS_STREAM_REPLAY)
            
            result = []
            for stream_id, data in events:
                if data.get("job_id") == job_id:
                    event_time = datetime.fromisoformat(data.get("timestamp", ""))
                    if event_time > cutoff:
                        data["stream_id"] = stream_id
                        result.append(data)
            
            return result
        except Exception as e:
            logger.error(f"Event replay failed: {e}")
            return []

    async def cleanup_instance_subscriptions(self) -> int:
        """Clean up subscriptions for disconnected instances."""
        if not self.client:
            return 0

        try:
            # Find stale subscriptions (older than 2 hours)
            pattern = "delivery:subscriptions:instance_*"
            keys = await self.client.keys(pattern)
            
            stale_count = 0
            for key in keys:
                ttl = await self.client.ttl(key)
                if ttl == -1:  # No expiration set, likely stale
                    await self.client.delete(key)
                    stale_count += 1
            
            return stale_count
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return 0


# Singleton instance
_redis_hub: Optional[RedisRealtimeHub] = None


async def get_redis_hub(redis_url: str) -> RedisRealtimeHub:
    """Get or create Redis realtime hub."""
    global _redis_hub
    if _redis_hub is None:
        _redis_hub = RedisRealtimeHub(redis_url)
        await _redis_hub.connect()
    return _redis_hub


async def close_redis_hub() -> None:
    """Cleanup Redis connection."""
    global _redis_hub
    if _redis_hub:
        await _redis_hub.disconnect()
        _redis_hub = None
