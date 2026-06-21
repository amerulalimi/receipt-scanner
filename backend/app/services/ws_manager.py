from __future__ import annotations

import asyncio
import logging
from typing import Any

from starlette.websockets import WebSocket

logger = logging.getLogger(__name__)


class DashboardWebSocketManager:
    """Manages desktop WebSocket subscriptions keyed by upload session token."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, token: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.setdefault(token, set()).add(websocket)

    async def unsubscribe(self, token: str, websocket: WebSocket) -> None:
        async with self._lock:
            connections = self._connections.get(token)
            if connections is None:
                return
            connections.discard(websocket)
            if not connections:
                del self._connections[token]

    async def emit(self, token: str, event: dict[str, Any]) -> None:
        async with self._lock:
            connections = list(self._connections.get(token, set()))

        stale: list[WebSocket] = []
        for websocket in connections:
            try:
                await websocket.send_json(event)
            except Exception:
                logger.debug("Removing stale WebSocket for token %s", token[:8])
                stale.append(websocket)

        for websocket in stale:
            await self.unsubscribe(token, websocket)


ws_manager = DashboardWebSocketManager()
