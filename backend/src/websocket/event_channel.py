from __future__ import annotations

from typing import Any

from .connection_manager import ConnectionManager


class EventChannel:
    def __init__(self, manager: ConnectionManager) -> None:
        self._manager = manager

    async def publish_event(self, tenant_id: str, event_name: str, payload: dict[str, Any]) -> None:
        import json

        await self._manager.send_to_tenant(
            tenant_id, json.dumps({"type": event_name, "payload": payload})
        )

