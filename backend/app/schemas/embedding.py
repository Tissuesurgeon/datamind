"""Search / embeddings request + response schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EmbedRequest(BaseModel):
    text: str = Field(min_length=1)


class EmbedResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    model: str
    dim: int
    vector: list[float]


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=512)
    limit: int = Field(default=10, ge=1, le=50)
    min_score: float = Field(default=0.5, ge=0.0, le=1.0)
    mode: Literal["semantic", "hybrid"] = "semantic"
    category: str | None = None


class SearchResult(BaseModel):
    dataset_id: str
    title: str
    category: str
    score: float
    snippet: str
    quality_grade: str | None
    embeddings_count: int
    owner_wallet: str


class SearchResponse(BaseModel):
    query: str
    mode: str
    took_ms: int
    results: list[SearchResult]
