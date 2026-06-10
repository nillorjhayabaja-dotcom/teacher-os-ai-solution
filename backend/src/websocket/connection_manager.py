from __future__ import annotations

import asyncio
from typing import Dict, Set


class ConnectionManager:
    """Manages active websocket connections.

    Foundational platform scaffold.
    """

    def __init__(self) -> None:
        self._connections: Set[object] = set()
        self._tenant_connections: Dict[str, Set[object]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: object, tenant_id: str) -> None:
        async with self._lock:
            self._connections.add(websocket)
            self._tenant_connections.setdefault(tenant_id, set()).add(websocket)

    async def disconnect(self, websocket: object, tenant_id: str) -> None:
        async with self._lock:
            self._connections.discard(websocket)
            if tenant_id in self._tenant_connections:
                self._tenant_connections[tenant_id].discard(websocket)

    async def broadcast(self, message: str) -> None:
        # websocket must implement `send_text`.
        targets = list(self._connections)
        for ws in targets:
            send = getattr(ws, "send_text", None)
            if callable(send):
                await send(message)

    async def send_to_tenant(self, tenant_id: str, message: str) -> None:
        targets = list(self._tenant_connections.get(tenant_id, set()))
        for ws in targets:
            send = getattr(ws, "send_text", None)
            if callable(send):
                await send(message)

