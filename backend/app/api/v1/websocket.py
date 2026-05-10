"""WebSocket fan-out — `/ws/{topic}` streams real-time events."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.services.realtime import get_ws_manager

router = APIRouter()
log = get_logger(__name__)


@router.websocket("/ws/{topic}")
async def websocket_endpoint(websocket: WebSocket, topic: str) -> None:
    await websocket.accept()
    manager = get_ws_manager()
    await manager.subscribe(topic, websocket)
    try:
        while True:
            # We don't expect messages from the client; just keep the connection alive.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # pragma: no cover
        log.warning("ws.error", error=str(exc), topic=topic)
    finally:
        await manager.unsubscribe(topic, websocket)
