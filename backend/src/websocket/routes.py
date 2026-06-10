from __future__ import annotations

from fastapi import APIRouter, WebSocket

from backend.src.websocket.connection_manager import ConnectionManager

router = APIRouter()


@router.websocket("/ws/notifications")
async def ws_notifications(websocket: WebSocket):
    await websocket.accept()
    # Foundational placeholder: tenant selection should come from AuthMiddleware.
    tenant_id = getattr(websocket, "tenant_id", "default")
    manager = ConnectionManager()
    await manager.connect(websocket, tenant_id)
    try:
        while True:
            await websocket.receive_text()
    finally:
        await manager.disconnect(websocket, tenant_id)

