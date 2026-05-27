from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Set, Optional

from fastapi import WebSocket
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisWebSocketBroker:
    """
    Redis Pub/Sub backed distributed WebSocket broker for horizontally-scaled backends.
    Syncs notifications and delivery events across multiple running FastAPI instances.
    """

    def __init__(self, redis_url: str) -> None:
        """
        Initialize the RedisWebSocketBroker instance.

        Args:
            redis_url: Connection URL to the Redis cluster or single node.
        """
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self._active_sockets: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
        logger.info("RedisWebSocketBroker initialized.")

    async def connect_redis(self) -> None:
        """
        Initialize connection to Redis client with keepalive sockets.
        Handles startup ping checks to verify connection integrity.
        """
        self.redis = await redis.from_url(
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
        await self.redis.ping()
        logger.info("WebSocket broker connected to Redis successfully.")

    async def disconnect_redis(self) -> None:
        """
        Gracefully close active Redis client connections on system shutdown.
        """
        if self.redis:
            await self.redis.close()
            logger.info("WebSocket broker Redis connection closed.")

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        """
        Register client WebSocket connection in local tracker.

        Args:
            user_id: Unique identifier for the client user.
            websocket: Actively opened FastAPI WebSocket connection structure.
        """
        async with self._lock:
            if user_id not in self._active_sockets:
                self._active_sockets[user_id] = set()
            self._active_sockets[user_id].add(websocket)
        logger.info(f"Local WebSocket connection registered for user_id={user_id}. Active sockets={len(self._active_sockets[user_id])}")

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        """
        Unregister and clean up inactive WebSocket connections from local tracker.

        Args:
            user_id: Unique identifier for the client user.
            websocket: Inactive or closed FastAPI WebSocket connection structure.
        """
        async with self._lock:
            if user_id in self._active_sockets:
                self._active_sockets[user_id].discard(websocket)
                if not self._active_sockets[user_id]:
                    del self._active_sockets[user_id]
        logger.info(f"Local WebSocket connection unregistered for user_id={user_id}.")

    async def publish(self, user_id: str, payload: Any, channel_prefix: str = "ws:notifications") -> None:
        """
        Publish JSON serializable payload to corresponding Redis channel.

        Args:
            user_id: Targeted user identifier.
            payload: JSON serializable Python dict/list to transmit.
            channel_prefix: Redis channel namespace (e.g. 'ws:notifications', 'ws:delivery').
        """
        if not self.redis:
            raise RuntimeError("WebSocket broker Redis client is not initialized or connected")
        
        channel = f"{channel_prefix}:{user_id}"
        serialized_payload = json.dumps(payload)
        await self.redis.publish(channel, serialized_payload)
        logger.info(f"Published event to channel={channel}")

    async def subscribe_and_forward(
        self,
        user_id: str,
        websocket: WebSocket,
        channel_prefix: str = "ws:notifications",
    ) -> None:
        """
        Subscribe to user Redis channel and dynamically forward incoming messages to
        the local active WebSocket connection. Handles Redis reconnection failures gracefully.

        Args:
            user_id: Unique identifier of the user.
            websocket: Actively opened client WebSocket.
            channel_prefix: Redis channel namespace (e.g. 'ws:notifications', 'ws:delivery').
        """
        if not self.redis:
            raise RuntimeError("WebSocket broker Redis client is not initialized or connected")

        channel = f"{channel_prefix}:{user_id}"
        logger.info(f"Subscribing to Redis channel={channel} for user_id={user_id}")

        while True:
            try:
                pubsub = self.redis.pubsub()
                await pubsub.subscribe(channel)
                logger.info(f"Active subscription established on channel={channel}")
                
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        data = message["data"]
                        try:
                            payload = json.loads(data)
                            await websocket.send_json(payload)
                            logger.debug(f"Forwarded payload to user_id={user_id} on channel={channel}")
                        except Exception as forward_err:
                            logger.error(f"Failed to forward message to user_id={user_id} on channel={channel}: {forward_err}")
            except (redis.ConnectionError, redis.TimeoutError) as conn_err:
                logger.warning(f"WebSocket broker lost Redis connection for user_id={user_id}: {conn_err}. Reconnecting in 2 seconds...")
                await asyncio.sleep(2)
                try:
                    await self.redis.ping()
                except Exception:
                    pass
            except asyncio.CancelledError:
                logger.info(f"Subscription task cancelled for user_id={user_id} on channel={channel}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in PubSub forward task for user_id={user_id}: {e}", exc_info=True)
                break
            finally:
                try:
                    await pubsub.unsubscribe(channel)
                    await pubsub.close()
                except Exception:
                    pass
