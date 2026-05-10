"""Vector index orchestration over Qdrant.

We talk to ai-engine for embedding and to Qdrant for storage. Both layers have
in-process fallbacks so the demo runs without either service.
"""

from __future__ import annotations

import asyncio
import uuid
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

from app.ai.client import get_ai_client
from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)

# In-memory vector store fallback used when Qdrant is unreachable.
_local_store: list[dict[str, Any]] = []
_local_lock = asyncio.Lock()


@dataclass
class _Hit:
    id: str
    score: float
    payload: dict[str, Any]


# --------------------------------------------------------------------------- #
# Qdrant helpers                                                              #
# --------------------------------------------------------------------------- #


def get_qdrant():
    settings = get_settings()
    try:
        from qdrant_client import AsyncQdrantClient

        return AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=(
                settings.qdrant_api_key.get_secret_value()
                if settings.qdrant_api_key
                else None
            ),
        )
    except Exception as exc:  # pragma: no cover
        log.warning("qdrant.client.init.failed", error=str(exc))
        return None


async def ensure_collection() -> None:
    settings = get_settings()
    client = get_qdrant()
    if client is None:
        return
    try:
        from qdrant_client.http.exceptions import UnexpectedResponse
        from qdrant_client.models import Distance, VectorParams

        try:
            await client.get_collection(settings.qdrant_collection)
        except (UnexpectedResponse, ValueError, Exception):
            await client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=VectorParams(
                    size=settings.qdrant_vector_size,
                    distance=Distance.COSINE,
                ),
            )
            log.info(
                "qdrant.collection.created",
                name=settings.qdrant_collection,
                size=settings.qdrant_vector_size,
            )
    finally:
        with suppress(Exception):
            await client.close()


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #


async def embed_text(text: str) -> tuple[list[float], str, int]:
    return await get_ai_client().embed(text)


async def index_chunks(
    *,
    dataset_id: str,
    owner_wallet: str,
    title: str,
    category: str,
    tags: list[str],
    chunks: list[str],
) -> int:
    """Embed `chunks` and upsert into Qdrant (or local fallback)."""
    if not chunks:
        return 0
    settings = get_settings()
    client = get_ai_client()
    vectors = await client.embed_batch(chunks)

    points = []
    for idx, (chunk, vec) in enumerate(zip(chunks, vectors)):
        point_id = str(uuid.uuid4())
        payload = {
            "dataset_id": dataset_id,
            "chunk_index": idx,
            "text": chunk[:1500],
            "title": title,
            "category": category,
            "tags": tags,
            "owner_wallet": owner_wallet,
        }
        points.append({"id": point_id, "vector": vec, "payload": payload})

    qdrant = get_qdrant()
    if qdrant is None:
        async with _local_lock:
            _local_store.extend(points)
        log.info("vectors.upserted.local", count=len(points), dataset=dataset_id)
        return len(points)

    try:
        from qdrant_client.models import PointStruct

        await qdrant.upsert(
            collection_name=settings.qdrant_collection,
            points=[
                PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"])
                for p in points
            ],
        )
        log.info("vectors.upserted.qdrant", count=len(points), dataset=dataset_id)
    except Exception as exc:  # pragma: no cover
        log.warning("qdrant.upsert.failed", error=str(exc))
        async with _local_lock:
            _local_store.extend(points)
    finally:
        with suppress(Exception):
            await qdrant.close()
    return len(points)


async def search_vectors(
    *,
    query_vector: list[float],
    limit: int = 10,
    min_score: float = 0.5,
    category: str | None = None,
) -> list[_Hit]:
    settings = get_settings()
    qdrant = get_qdrant()
    if qdrant is not None:
        try:
            from qdrant_client.models import FieldCondition, Filter, MatchValue

            qfilter = None
            if category and category.lower() != "all":
                qfilter = Filter(
                    must=[FieldCondition(key="category", match=MatchValue(value=category))]
                )
            res = await qdrant.search(
                collection_name=settings.qdrant_collection,
                query_vector=query_vector,
                limit=limit,
                score_threshold=min_score,
                query_filter=qfilter,
            )
            return [
                _Hit(id=str(p.id), score=float(p.score or 0), payload=dict(p.payload or {}))
                for p in res
            ]
        except Exception as exc:
            log.warning("qdrant.search.failed", error=str(exc))
        finally:
            with suppress(Exception):
                await qdrant.close()

    # Local fallback — cosine in pure Python (small N).
    async with _local_lock:
        candidates = list(_local_store)
    if not candidates:
        return []

    def _cos(a: list[float], b: list[float]) -> float:
        num = sum(x * y for x, y in zip(a, b))
        da = sum(x * x for x in a) ** 0.5 or 1.0
        db = sum(y * y for y in b) ** 0.5 or 1.0
        return num / (da * db)

    scored: list[tuple[float, dict]] = []
    for p in candidates:
        if category and category.lower() != "all":
            if p["payload"].get("category") != category:
                continue
        s = _cos(query_vector, p["vector"])
        if s >= min_score:
            scored.append((s, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    hits = scored[:limit]
    return [_Hit(id=p["id"], score=s, payload=dict(p["payload"])) for s, p in hits]
