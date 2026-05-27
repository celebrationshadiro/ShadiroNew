from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Dict, Set

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[channel].add(websocket)

    async def disconnect(self, channel: str, websocket: WebSocket) -> None:
        async with self._lock:
            if channel in self._connections:
                self._connections[channel].discard(websocket)
                if not self._connections[channel]:
                    del self._connections[channel]

    async def broadcast(self, channel: str, payload: dict) -> None:
        stale: Set[WebSocket] = set()
        async with self._lock:
            clients = list(self._connections.get(channel, set()))
        for ws in clients:
            try:
                await ws.send_json(payload)
            except Exception:
                stale.add(ws)
        if stale:
            async with self._lock:
                for ws in stale:
                    self._connections[channel].discard(ws)

