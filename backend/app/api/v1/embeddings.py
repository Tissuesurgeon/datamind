"""Embeddings endpoint — proxies to ai-engine."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.embedding import EmbedRequest, EmbedResponse
from app.services.embeddings.indexer import embed_text

router = APIRouter()


@router.post("/embed", response_model=EmbedResponse)
async def embed(req: EmbedRequest) -> EmbedResponse:
    vec, model, dim = await embed_text(req.text)
    return EmbedResponse(model=model, dim=dim, vector=vec)
