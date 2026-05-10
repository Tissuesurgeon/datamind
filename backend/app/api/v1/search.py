"""Search endpoints — semantic + hybrid."""

from __future__ import annotations

import time

from fastapi import APIRouter

from app.core.deps import DBSession
from app.schemas.embedding import SearchRequest, SearchResponse
from app.services.search.semantic import semantic_search
from app.services.search.hybrid import hybrid_search

router = APIRouter()


@router.post("/semantic", response_model=SearchResponse)
async def search_semantic(req: SearchRequest, db: DBSession) -> SearchResponse:
    start = time.perf_counter()
    results = await semantic_search(
        db, query=req.query, limit=req.limit, min_score=req.min_score, category=req.category
    )
    return SearchResponse(
        query=req.query,
        mode="semantic",
        took_ms=int((time.perf_counter() - start) * 1000),
        results=results,
    )


@router.post("/hybrid", response_model=SearchResponse)
async def search_hybrid(req: SearchRequest, db: DBSession) -> SearchResponse:
    start = time.perf_counter()
    results = await hybrid_search(
        db, query=req.query, limit=req.limit, min_score=req.min_score, category=req.category
    )
    return SearchResponse(
        query=req.query,
        mode="hybrid",
        took_ms=int((time.perf_counter() - start) * 1000),
        results=results,
    )
