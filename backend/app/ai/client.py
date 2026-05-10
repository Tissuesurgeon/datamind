"""HTTP client for the standalone ai-engine service.

The backend never imports torch/transformers directly. Heavy ML stays in
`ai-engine/` and we cross the process boundary via this client.

If the ai-engine service is unreachable, the client falls back to a
deterministic in-process embedder so the demo always works.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

import httpx
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


@dataclass
class AnalyzeResult:
    summary: str
    semantic_tags: list[str]
    topics: list[dict]
    quality_metrics: dict
    duplicate_ratio: float
    missing_ratio: float
    column_profile: dict
    sample_rows: list[dict]
    rows: int
    columns: int
    quality_score: float
    ai_readiness: float
    quality_grade: str


class AIEngineClient:
    """Thin async wrapper around the ai-engine HTTP API."""

    def __init__(self, base_url: str | None = None) -> None:
        settings = get_settings()
        self._base = (base_url or settings.ai_engine_url).rstrip("/")
        self._client = httpx.AsyncClient(timeout=120, base_url=self._base)
        self._dim = settings.qdrant_vector_size
        self._model = settings.ai_embedding_model

    @property
    def model(self) -> str:
        return self._model

    @property
    def dim(self) -> int:
        return self._dim

    async def aclose(self) -> None:
        await self._client.aclose()

    # ---- low-level retrying call -------------------------------------------

    async def _call(self, method: str, path: str, **kwargs):
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(2),
            wait=wait_exponential(multiplier=0.4, max=2),
            reraise=True,
        ):
            with attempt:
                resp = await self._client.request(method, path, **kwargs)
                resp.raise_for_status()
                return resp.json()
        return None  # pragma: no cover

    # ---- public API --------------------------------------------------------

    async def healthz(self) -> bool:
        try:
            r = await self._client.get("/healthz", timeout=4)
            return r.status_code == 200
        except Exception:
            return False

    async def embed(self, text: str) -> tuple[list[float], str, int]:
        try:
            data = await self._call("POST", "/embed", json={"text": text})
            return data["vector"], data["model"], data["dim"]
        except Exception as exc:
            log.debug("ai.embed.fallback", error=str(exc))
            return self._fallback_embed(text), self._model, self._dim

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        try:
            data = await self._call("POST", "/embed/batch", json={"texts": texts})
            return data["vectors"]
        except Exception as exc:
            log.debug("ai.embed_batch.fallback", error=str(exc))
            return [self._fallback_embed(t) for t in texts]

    async def analyze(self, *, path: str, format: str) -> AnalyzeResult:
        try:
            data = await self._call(
                "POST", "/analyze", json={"path": path, "format": format}
            )
            return AnalyzeResult(**data)
        except Exception as exc:
            log.warning("ai.analyze.fallback", error=str(exc))
            return self._fallback_analyze(path)

    async def chunk(self, *, path: str, format: str, max_tokens: int = 256) -> list[str]:
        try:
            data = await self._call(
                "POST",
                "/chunk",
                json={"path": path, "format": format, "max_tokens": max_tokens},
            )
            return data["chunks"]
        except Exception as exc:
            log.warning("ai.chunk.fallback", error=str(exc))
            return self._fallback_chunk(path, max_tokens)

    async def train(self, *, job_id: str, config: dict) -> dict:
        return await self._call("POST", "/train", json={"job_id": job_id, "config": config})

    # ---- deterministic fallbacks --------------------------------------------

    def _fallback_embed(self, text: str) -> list[float]:
        """Deterministic mock embedding: hash → bytes → 384 float32 in [-1,1]."""
        if not text:
            text = " "
        seed = hashlib.sha512(text.encode("utf-8")).digest()
        # Repeat the hash until we have enough bytes for `dim` floats.
        buf = b""
        while len(buf) < self._dim * 4:
            seed = hashlib.sha512(seed).digest()
            buf += seed
        ints = [int.from_bytes(buf[i : i + 4], "big", signed=False) for i in range(0, self._dim * 4, 4)]
        floats = [(i / 0xFFFFFFFF) * 2.0 - 1.0 for i in ints]
        # L2-normalize
        norm = math.sqrt(sum(f * f for f in floats)) or 1.0
        return [f / norm for f in floats]

    def _fallback_analyze(self, path: str) -> AnalyzeResult:
        return AnalyzeResult(
            summary=(
                "Auto-generated summary unavailable (ai-engine offline). "
                "This dataset is registered with placeholder analytics."
            ),
            semantic_tags=["unprocessed"],
            topics=[],
            quality_metrics={"completeness": 0.5, "uniqueness": 0.5, "schema": 0.5},
            duplicate_ratio=0.0,
            missing_ratio=0.0,
            column_profile={},
            sample_rows=[],
            rows=0,
            columns=0,
            quality_score=0.5,
            ai_readiness=0.5,
            quality_grade="C",
        )

    def _fallback_chunk(self, path: str, max_tokens: int) -> list[str]:
        try:
            with open(path, encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
        except Exception:
            return []
        approx_chars = max_tokens * 4
        return [text[i : i + approx_chars] for i in range(0, len(text), approx_chars)] or [text]


_singleton: AIEngineClient | None = None


def get_ai_client() -> AIEngineClient:
    global _singleton
    if _singleton is None:
        _singleton = AIEngineClient()
    return _singleton
