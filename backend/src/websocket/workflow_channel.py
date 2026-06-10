from __future__ import annotations

from typing import Any

from .connection_manager import ConnectionManager


class WorkflowChannel:
    def __init__(self, manager: ConnectionManager) -> None:
        self._manager = manager

    async def publish_workflow_update(
        self,
        tenant_id: str,
        workflow_id: str,
        state: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        import json

        await self._manager.send_to_tenant(
            tenant_id,
            json.dumps(
                {
                    "type": "workflow.update",
                    "payload": {
                        "workflow_id": workflow_id,
                        "state": state,
                        "payload": payload or {},
                    },
                }
            ),
        )

