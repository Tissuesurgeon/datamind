"""DataMind AI engine FastAPI server.

Endpoints:
    GET  /healthz
    POST /embed                {text}                  -> {model, dim, vector}
    POST /embed/batch          {texts: [..]}           -> {model, dim, vectors}
    POST /chunk                {path, format, max_tokens?} -> {chunks: [..]}
    POST /analyze              {path, format?, title?} -> AnalyzeResult
    POST /train                {job_id, dataset_id?, base_model, config}
                                — returns NDJSON stream of progress events.
    POST /infer                {prompt, base_model?}   -> {output, ...}
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from datamind_ai import __version__
from datamind_ai.config import get_config
from datamind_ai.embeddings import embed_many, embed_one, get_dim, get_model_name, is_real_model
from datamind_ai.inference import quick_predict
from datamind_ai.pipelines import analyze_dataset
from datamind_ai.training.config import TrainingConfig
from datamind_ai.training.trainer import run_training


# ---- Schemas ---------------------------------------------------------------- #


class EmbedReq(BaseModel):
    text: str = Field(min_length=1)


class EmbedResp(BaseModel):
    model_config = {"protected_namespaces": ()}

    model: str
    dim: int
    vector: list[float]


class EmbedBatchReq(BaseModel):
    texts: list[str]


class EmbedBatchResp(BaseModel):
    model_config = {"protected_namespaces": ()}

    model: str
    dim: int
    vectors: list[list[float]]


class ChunkReq(BaseModel):
    path: str
    format: str | None = None
    max_tokens: int = 256


class ChunkResp(BaseModel):
    chunks: list[str]


class AnalyzeReq(BaseModel):
    path: str
    format: str | None = None
    title: str = ""


class TrainReq(BaseModel):
    model_config = {"protected_namespaces": ()}

    job_id: str
    dataset_id: str | None = None
    base_model: str | None = None
    config: dict = Field(default_factory=dict)


class InferReq(BaseModel):
    model_config = {"protected_namespaces": ()}

    prompt: str
    base_model: str | None = None


# ---- App -------------------------------------------------------------------- #


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Trigger lazy-load on boot so the first user request is fast.
    _ = get_model_name()
    yield


app = FastAPI(
    title="DataMind AI Engine",
    version=__version__,
    lifespan=lifespan,
)


@app.get("/healthz")
async def healthz() -> dict:
    return {
        "status": "ok",
        "version": __version__,
        "model": get_model_name(),
        "dim": get_dim(),
        "real_model": is_real_model(),
    }


@app.post("/embed", response_model=EmbedResp)
async def embed_endpoint(req: EmbedReq) -> EmbedResp:
    return EmbedResp(model=get_model_name(), dim=get_dim(), vector=embed_one(req.text))


@app.post("/embed/batch", response_model=EmbedBatchResp)
async def embed_batch_endpoint(req: EmbedBatchReq) -> EmbedBatchResp:
    if not req.texts:
        return EmbedBatchResp(model=get_model_name(), dim=get_dim(), vectors=[])
    return EmbedBatchResp(model=get_model_name(), dim=get_dim(), vectors=embed_many(req.texts))


@app.post("/chunk", response_model=ChunkResp)
async def chunk_endpoint(req: ChunkReq) -> ChunkResp:
    p = Path(req.path)
    if not p.exists():
        return ChunkResp(chunks=[])
    text = p.read_text(encoding="utf-8", errors="ignore")
    approx_chars = max(req.max_tokens, 64) * 4
    chunks = [text[i : i + approx_chars] for i in range(0, len(text), approx_chars)]
    return ChunkResp(chunks=chunks or [text])


@app.post("/analyze")
async def analyze_endpoint(req: AnalyzeReq) -> dict:
    p = Path(req.path)
    if not p.exists():
        return {
            "summary": "File not found.",
            "semantic_tags": [],
            "topics": [],
            "quality_metrics": {},
            "duplicate_ratio": 0.0,
            "missing_ratio": 0.0,
            "column_profile": {},
            "sample_rows": [],
            "rows": 0,
            "columns": 0,
            "quality_score": 0.0,
            "ai_readiness": 0.0,
            "quality_grade": "C",
        }
    result = analyze_dataset(p, req.format, title=req.title)
    return result.to_dict()


@app.post("/train")
async def train_endpoint(req: TrainReq) -> StreamingResponse:
    cfg = get_config()
    base = req.base_model or req.config.get("base_model") or cfg.default_base_model
    train_cfg = TrainingConfig(
        job_id=req.job_id,
        base_model=base,
        epochs=int(req.config.get("epochs", 3)),
        batch_size=int(req.config.get("batch_size", 4)),
        learning_rate=float(req.config.get("learning_rate", 2e-4)),
        lora_r=int(req.config.get("lora_r", 8)),
        lora_alpha=int(req.config.get("lora_alpha", 16)),
        max_seq_length=int(req.config.get("max_seq_length", 512)),
    )

    async def stream() -> AsyncIterator[bytes]:
        async for evt in run_training(train_cfg):
            yield (json.dumps(evt) + "\n").encode("utf-8")

    return StreamingResponse(stream(), media_type="application/x-ndjson")


@app.post("/infer")
async def infer_endpoint(req: InferReq) -> dict:
    cfg = get_config()
    return quick_predict(req.prompt, req.base_model or cfg.default_base_model)
