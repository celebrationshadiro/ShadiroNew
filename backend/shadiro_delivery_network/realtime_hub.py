from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, DefaultDict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class DeliveryRealtimeHub:
    """In-process fan-out for delivery WebSockets (horizontal scale via Redis adapter later)."""

    def __init__(self) -> None:
        self._by_user: DefaultDict[str, Set[WebSocket]] = defaultdict(set)
        self._by_job: DefaultDict[str, Set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def register_user_socket(self, user_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._by_user[str(user_id)].add(websocket)

    async def unregister_user_socket(self, user_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._by_user[str(user_id)].discard(websocket)
            if not self._by_user[str(user_id)]:
                del self._by_user[str(user_id)]

    async def subscribe_job(self, job_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._by_job[str(job_id)].add(websocket)

    async def unsubscribe_job(self, job_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._by_job[str(job_id)].discard(websocket)
            if not self._by_job[str(job_id)]:
                del self._by_job[str(job_id)]

    async def _send_safe(self, ws: WebSocket, payload: dict[str, Any]) -> bool:
        try:
            await ws.send_json(payload)
            return True
        except Exception:
            logger.debug("delivery_ws_send_failed", exc_info=True)
            return False

    async def publish_to_user(self, user_id: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            targets = list(self._by_user.get(str(user_id), set()))
        stale: list[tuple[str, WebSocket]] = []
        for ws in targets:
            if not await self._send_safe(ws, payload):
                stale.append((str(user_id), ws))
        if stale:
            async with self._lock:
                for uid, ws in stale:
                    self._by_user[uid].discard(ws)

    async def publish_to_job(self, job_id: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            targets = list(self._by_job.get(str(job_id), set()))
        stale: list[WebSocket] = []
        for ws in targets:
            if not await self._send_safe(ws, payload):
                stale.append(ws)
        if stale:
            async with self._lock:
                for ws in stale:
                    self._by_job[str(job_id)].discard(ws)
