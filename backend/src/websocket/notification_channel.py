from __future__ import annotations

from .connection_manager import ConnectionManager


class NotificationChannel:
    def __init__(self, manager: ConnectionManager) -> None:
        self._manager = manager

    async def notify(self, tenant_id: str, payload: dict) -> None:
        import json

        await self._manager.send_to_tenant(tenant_id, json.dumps(payload))

