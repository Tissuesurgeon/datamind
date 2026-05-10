"""0G Compute job runner abstraction.

Production-oriented interface — `submit / poll / cancel / stream_logs`.
Two implementations:
    LocalRunner       — executes via ai-engine HTTP (default).
    OGComputeRunner   — HTTP stub against the Galileo compute endpoint.
                        Real wiring lives behind a feature flag; the structure
                        is here so we can flip from local to 0G Compute by
                        env var alone.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


class JobKind(str, Enum):
    EMBEDDING = "embedding"
    TRAINING = "training"
    INFERENCE = "inference"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobHandle:
    id: str
    kind: JobKind
    status: JobStatus = JobStatus.PENDING
    result: dict[str, Any] = field(default_factory=dict)


class JobRunner(Protocol):
    async def submit(self, *, kind: JobKind, payload: dict[str, Any]) -> JobHandle: ...
    async def poll(self, job_id: str) -> JobHandle: ...
    async def cancel(self, job_id: str) -> JobHandle: ...
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]: ...


# --------------------------------------------------------------------------- #
# Local runner — uses ai-engine HTTP API.                                     #
# --------------------------------------------------------------------------- #


class LocalRunner:
    def __init__(self) -> None:
        self._jobs: dict[str, JobHandle] = {}

    async def submit(self, *, kind: JobKind, payload: dict[str, Any]) -> JobHandle:
        from app.utils.ids import new_ulid

        handle = JobHandle(id=new_ulid(), kind=kind, status=JobStatus.PENDING)
        self._jobs[handle.id] = handle
        asyncio.create_task(self._run(handle, payload))
        return handle

    async def _run(self, handle: JobHandle, payload: dict[str, Any]) -> None:
        settings = get_settings()
        url = settings.ai_engine_url.rstrip("/")
        handle.status = JobStatus.RUNNING
        try:
            async with httpx.AsyncClient(timeout=300) as client:
                if handle.kind == JobKind.EMBEDDING:
                    r = await client.post(f"{url}/embed/batch", json=payload)
                    handle.result = r.json()
                elif handle.kind == JobKind.INFERENCE:
                    r = await client.post(f"{url}/infer", json=payload)
                    handle.result = r.json()
                elif handle.kind == JobKind.TRAINING:
                    # Training is streamed; collect events.
                    events: list[dict] = []
                    async with client.stream("POST", f"{url}/train", json=payload) as resp:
                        async for line in resp.aiter_lines():
                            if line:
                                try:
                                    import json as _json

                                    events.append(_json.loads(line))
                                except Exception:
                                    pass
                    handle.result = {"events": events[-50:]}
            handle.status = JobStatus.SUCCEEDED
        except Exception as exc:  # pragma: no cover
            log.warning("local_runner.failed", error=str(exc))
            handle.status = JobStatus.FAILED
            handle.result = {"error": str(exc)}

    async def poll(self, job_id: str) -> JobHandle:
        return self._jobs.get(
            job_id, JobHandle(id=job_id, kind=JobKind.INFERENCE, status=JobStatus.FAILED)
        )

    async def cancel(self, job_id: str) -> JobHandle:
        handle = self._jobs.get(job_id)
        if handle is None:
            return JobHandle(id=job_id, kind=JobKind.INFERENCE, status=JobStatus.FAILED)
        handle.status = JobStatus.CANCELLED
        return handle

    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        handle = self._jobs.get(job_id)
        if handle is None:
            return
        # Local runner doesn't have a separate log stream; we yield the result keys.
        for evt in handle.result.get("events", []):
            yield str(evt)


# --------------------------------------------------------------------------- #
# 0G Compute runner — production-oriented stub.                                #
# --------------------------------------------------------------------------- #


class OGComputeRunner:
    """HTTP stub against the 0G Compute endpoint.

    The 0G Compute network exposes a job-scheduler API similar in shape to
    the LocalRunner; until we have stable Galileo endpoints, this class
    delegates to LocalRunner so calls succeed in any environment.
    """

    def __init__(self, base_url: str | None = None) -> None:
        self._base = (base_url or "https://compute-testnet.0g.ai").rstrip("/")
        self._fallback = LocalRunner()

    async def submit(self, *, kind: JobKind, payload: dict[str, Any]) -> JobHandle:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(
                    f"{self._base}/v1/jobs",
                    json={"kind": kind.value, "payload": payload},
                )
                if r.status_code < 400:
                    data = r.json()
                    return JobHandle(
                        id=str(data.get("id")),
                        kind=kind,
                        status=JobStatus(data.get("status", "pending")),
                        result=data.get("result", {}),
                    )
        except Exception as exc:
            log.info("og_compute.submit.unreachable", error=str(exc))
        return await self._fallback.submit(kind=kind, payload=payload)

    async def poll(self, job_id: str) -> JobHandle:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{self._base}/v1/jobs/{job_id}")
                if r.status_code < 400:
                    data = r.json()
                    return JobHandle(
                        id=str(data.get("id", job_id)),
                        kind=JobKind(data.get("kind", "inference")),
                        status=JobStatus(data.get("status", "pending")),
                        result=data.get("result", {}),
                    )
        except Exception:
            pass
        return await self._fallback.poll(job_id)

    async def cancel(self, job_id: str) -> JobHandle:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(f"{self._base}/v1/jobs/{job_id}/cancel")
        except Exception:
            pass
        return await self._fallback.cancel(job_id)

    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        # Streaming logs from 0G Compute would go here — fall back for now.
        async for line in self._fallback.stream_logs(job_id):
            yield line


# --------------------------------------------------------------------------- #
# Singleton selector                                                          #
# --------------------------------------------------------------------------- #


_singleton: JobRunner | None = None


def get_runner() -> JobRunner:
    global _singleton
    if _singleton is not None:
        return _singleton
    settings = get_settings()
    if settings.og_mock or settings.og_private_key is None:
        _singleton = LocalRunner()
    else:
        _singleton = OGComputeRunner()
    return _singleton
