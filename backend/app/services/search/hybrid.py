"""Hybrid search — semantic top-K reranked with keyword overlap."""

from __future__ import annotations

import re

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dataset import Dataset, DatasetStatus, DatasetVisibility
from app.schemas.embedding import SearchResult
from app.services.search.semantic import semantic_search


def _keyword_score(query: str, text: str) -> float:
    qtokens = {t.lower() for t in re.findall(r"\w+", query) if len(t) > 2}
    if not qtokens:
        return 0.0
    htokens = {t.lower() for t in re.findall(r"\w+", text)}
    if not htokens:
        return 0.0
    overlap = qtokens & htokens
    return len(overlap) / max(len(qtokens), 1)


async def hybrid_search(
    db: AsyncSession,
    *,
    query: str,
    limit: int = 10,
    min_score: float = 0.4,
    category: str | None = None,
) -> list[SearchResult]:
    semantic = await semantic_search(
        db, query=query, limit=limit * 2, min_score=min_score, category=category
    )

    # Postgres-side keyword fallback for datasets that have NO embeddings yet
    # (e.g. just-uploaded). Adds breadth without sacrificing relevance.
    pattern = f"%{query.lower()}%"
    stmt = (
        select(Dataset)
        .options(selectinload(Dataset.owner))
        .where(
            Dataset.visibility == DatasetVisibility.PUBLIC,
            Dataset.status == DatasetStatus.READY,
            or_(
                Dataset.title.ilike(pattern),
                Dataset.description.ilike(pattern),
                Dataset.category.ilike(pattern),
            ),
        )
        .limit(limit * 2)
    )
    res = await db.execute(stmt)
    keyword_rows = res.scalars().all()
    seen = {r.dataset_id for r in semantic}

    boosted = list(semantic)
    for d in keyword_rows:
        if d.id in seen:
            continue
        # Synthesize a result from the row metadata.
        text = " ".join([d.title or "", d.description or "", " ".join(d.tags or [])])
        score = _keyword_score(query, text) * 0.6  # capped below typical semantic
        if score < min_score:
            continue
        boosted.append(
            SearchResult(
                dataset_id=d.id,
                title=d.title,
                category=d.category,
                score=round(score, 4),
                snippet=(d.description or "")[:280],
                quality_grade=d.quality_grade,
                embeddings_count=d.embeddings_count,
                owner_wallet=d.owner.wallet_address if d.owner else "",
            )
        )

    # Re-rank with a 0.85 semantic / 0.15 keyword blend.
    for r in boosted:
        kw = _keyword_score(query, f"{r.title} {r.snippet}")
        r.score = round(r.score * 0.85 + kw * 0.15, 4)

    boosted.sort(key=lambda r: r.score, reverse=True)
    # Deduplicate by dataset_id, keeping highest score.
    out: list[SearchResult] = []
    seen_ids: set[str] = set()
    for r in boosted:
        if r.dataset_id in seen_ids:
            continue
        seen_ids.add(r.dataset_id)
        out.append(r)
    return out[:limit]
