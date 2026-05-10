"""Pure-vector semantic search."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.client import get_ai_client
from app.models.dataset import Dataset
from app.schemas.embedding import SearchResult
from app.services.embeddings.indexer import search_vectors


async def semantic_search(
    db: AsyncSession,
    *,
    query: str,
    limit: int = 10,
    min_score: float = 0.5,
    category: str | None = None,
) -> list[SearchResult]:
    if not query.strip():
        return []
    ai = get_ai_client()
    qvec, _, _ = await ai.embed(query)
    hits = await search_vectors(
        query_vector=qvec, limit=limit * 3, min_score=min_score, category=category
    )

    # Group hits by dataset_id keeping the best score per dataset.
    by_ds: dict[str, tuple[float, str]] = {}
    for h in hits:
        ds_id = h.payload.get("dataset_id")
        if not ds_id:
            continue
        snippet = (h.payload.get("text") or "")[:280]
        prev = by_ds.get(ds_id)
        if prev is None or h.score > prev[0]:
            by_ds[ds_id] = (h.score, snippet)

    if not by_ds:
        return []

    res = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.owner))
        .where(Dataset.id.in_(by_ds.keys()))
    )
    rows = {d.id: d for d in res.scalars().all()}

    out: list[SearchResult] = []
    for ds_id, (score, snippet) in by_ds.items():
        d = rows.get(ds_id)
        if d is None:
            continue
        out.append(
            SearchResult(
                dataset_id=d.id,
                title=d.title,
                category=d.category,
                score=round(score, 4),
                snippet=snippet,
                quality_grade=d.quality_grade,
                embeddings_count=d.embeddings_count,
                owner_wallet=d.owner.wallet_address if d.owner else "",
            )
        )
    out.sort(key=lambda r: r.score, reverse=True)
    return out[:limit]
