"""WebSocket fan-out manager backed by Redis pubsub.

Workers (running in any process) call `publish(event)` and connected WS clients
subscribed to that topic receive the payload in real time.

Falls back to an in-process broadcast if Redis is unavailable, so the demo
still works in fully-mocked mode.
"""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import suppress

import redis.asyncio as aioredis
from fastapi import WebSocket

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.realtime.events import RealtimeEvent

log = get_logger(__name__)

_PUBSUB_CHANNEL = "datamind.events"


class WebSocketManager:
    """Singleton fan-out manager. Use `get_ws_manager()` to access it."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()
        self._redis: aioredis.Redis | None = None
        self._listener: asyncio.Task | None = None
        self._started = False

    # ---- lifecycle ----------------------------------------------------------

    async def start(self) -> None:
        if self._started:
            return
        self._started = True
        settings = get_settings()
        try:
            self._redis = aioredis.from_url(
                settings.redis_url, encoding="utf-8", decode_responses=True
            )
            await self._redis.ping()
            self._listener = asyncio.create_task(self._listen_redis())
            log.info("ws_manager.redis.connected", url=settings.redis_url)
        except Exception as exc:  # pragma: no cover — best-effort
            log.warning("ws_manager.redis.unavailable", error=str(exc))
            self._redis = None

    async def shutdown(self) -> None:
        if self._listener is not None:
            self._listener.cancel()
            with suppress(asyncio.CancelledError):
                await self._listener
            self._listener = None
        if self._redis is not None:
            with suppress(Exception):
                await self._redis.close()
            self._redis = None
        async with self._lock:
            for sockets in self._connections.values():
                for ws in list(sockets):
                    with suppress(Exception):
                        await ws.close()
            self._connections.clear()
        self._started = False

    # ---- subscribe / unsubscribe -------------------------------------------

    async def subscribe(self, topic: str, ws: WebSocket) -> None:
        async with self._lock:
            self._connections[topic].add(ws)

    async def unsubscribe(self, topic: str, ws: WebSocket) -> None:
        async with self._lock:
            self._connections[topic].discard(ws)
            if not self._connections[topic]:
                del self._connections[topic]

    # ---- publish / broadcast -----------------------------------------------

    async def publish(self, event: RealtimeEvent) -> None:
        """Fan out an event. Goes through Redis if available, else in-process."""
        msg = json.dumps(event.to_json())
        if self._redis is not None:
            with suppress(Exception):
                await self._redis.publish(_PUBSUB_CHANNEL, msg)
                return
        await self._broadcast_local(event.topic, msg)

    async def _broadcast_local(self, topic: str, payload: str) -> None:
        async with self._lock:
            sockets = list(self._connections.get(topic, []))
        await self._send_many(sockets, payload)

    async def _send_many(self, sockets: list[WebSocket], payload: str) -> None:
        for ws in sockets:
            try:
                await ws.send_text(payload)
            except Exception as exc:  # pragma: no cover
                log.debug("ws_manager.send.failed", error=str(exc))

    # ---- redis listener -----------------------------------------------------

    async def _listen_redis(self) -> None:
        assert self._redis is not None
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(_PUBSUB_CHANNEL)
        try:
            async for msg in pubsub.listen():
                if msg.get("type") != "message":
                    continue
                payload = msg.get("data")
                if not isinstance(payload, str):
                    continue
                try:
                    parsed = json.loads(payload)
                    topic = parsed.get("topic")
                except Exception:
                    continue
                if not topic:
                    continue
                async with self._lock:
                    sockets = list(self._connections.get(topic, []))
                if sockets:
                    await self._send_many(sockets, payload)
        except asyncio.CancelledError:
            pass
        finally:
            with suppress(Exception):
                await pubsub.unsubscribe(_PUBSUB_CHANNEL)
                await pubsub.close()

    # ---- iteration ---------------------------------------------------------

    async def stream(self, topic: str, ws: WebSocket) -> AsyncIterator[None]:
        await self.subscribe(topic, ws)
        try:
            yield
        finally:
            await self.unsubscribe(topic, ws)


_singleton: WebSocketManager | None = None


def get_ws_manager() -> WebSocketManager:
    global _singleton
    if _singleton is None:
        _singleton = WebSocketManager()
    return _singleton
