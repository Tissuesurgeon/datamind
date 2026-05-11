"""Dataset ingest pipeline.

Stages:
    1. record DatasetFile (sha256 + local path)
    2. AI analyze (rows/cols, quality, tags, summary, sample rows)
    3. chunk + embed + index in Qdrant
    4. push to 0G Storage (mock or live)
    5. register on-chain in DatasetRegistry (mock or live)

Each stage publishes a RealtimeEvent so the frontend can show live progress.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.client import AnalyzeResult, get_ai_client
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import session_scope
from app.models.dataset import Dataset, DatasetFile, DatasetStatus
from app.models.dataset_analytics import DatasetAnalytics
from app.services.chain import registry as chain_registry
from app.services.embeddings.chunker import chunk_file
from app.services.embeddings.indexer import index_chunks
from app.services.realtime import EventType, RealtimeEvent, get_ws_manager
from app.services.storage import og_client

log = get_logger(__name__)


# --------------------------------------------------------------------------- #
# Synchronous prep — called inside the upload request transaction.            #
# --------------------------------------------------------------------------- #


async def ingest_dataset(
    db: AsyncSession,
    *,
    dataset: Dataset,
    local_path: Path,
    sha256: str,
    size: int,
    mime: str,
    original_filename: str,
) -> DatasetFile:
    """Persist DatasetFile row + flip dataset to PROCESSING."""
    f = DatasetFile(
        dataset_id=dataset.id,
        filename=original_filename,
        mime_type=mime,
        size_bytes=size,
        sha256=sha256,
        local_path=str(local_path),
    )
    db.add(f)
    dataset.size_bytes = size
    dataset.status = DatasetStatus.PROCESSING
    dataset.progress = 5
    return f


# --------------------------------------------------------------------------- #
# Async pipeline — runs after the response returns to the client.             #
# --------------------------------------------------------------------------- #


async def _publish(topic: str, type_: EventType, payload: dict[str, Any]) -> None:
    await get_ws_manager().publish(RealtimeEvent(type=type_, topic=topic, payload=payload))


def _grade(score: float) -> str:
    if score >= 0.85:
        return "A"
    if score >= 0.65:
        return "B"
    return "C"


async def _set_progress(
    db: AsyncSession, dataset_id: str, progress: int, status: DatasetStatus | None = None
) -> None:
    res = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    d = res.scalar_one_or_none()
    if d is None:
        return
    d.progress = max(min(progress, 100), 0)
    if status is not None:
        d.status = status


async def run_pipeline_in_background(dataset_id: str) -> None:
    """FastAPI BackgroundTasks entrypoint — owns its own DB session."""
    try:
        await run_ingest_pipeline(dataset_id)
    except Exception as exc:  # pragma: no cover
        log.exception("ingest.failed", dataset_id=dataset_id, error=str(exc))
        async with session_scope() as db:
            res = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
            d = res.scalar_one_or_none()
            if d is not None:
                d.status = DatasetStatus.FAILED
                d.progress = 100
        await _publish(
            f"dataset:{dataset_id}",
            EventType.UPLOAD_FAILED,
            {"error": str(exc)},
        )


async def run_ingest_pipeline(dataset_id: str) -> None:
    topic = f"dataset:{dataset_id}"
    await _publish(topic, EventType.UPLOAD_STARTED, {"dataset_id": dataset_id})

    # ---- Load dataset + file -------------------------------------------------
    async with session_scope() as db:
        res = await db.execute(
            select(Dataset)
            .options(selectinload(Dataset.files), selectinload(Dataset.owner))
            .where(Dataset.id == dataset_id)
        )
        dataset = res.scalar_one_or_none()
        if dataset is None:
            log.warning("ingest.missing.dataset", id=dataset_id)
            return
        file = dataset.files[0] if dataset.files else None
        if file is None or not file.local_path:
            log.warning("ingest.missing.file", id=dataset_id)
            return
        local_path = Path(file.local_path)
        owner_wallet = dataset.owner.wallet_address if dataset.owner else ""
        title = dataset.title
        category = dataset.category
        tags = list(dataset.tags or [])
        format_ = dataset.format

    # ---- Analyze -------------------------------------------------------------
    await _publish(topic, EventType.ANALYZE_STARTED, {"path": str(local_path)})
    ai = get_ai_client()
    analyze: AnalyzeResult = await ai.analyze(path=str(local_path), format=format_)
    await _publish(
        topic,
        EventType.ANALYZE_COMPLETED,
        {
            "rows": analyze.rows,
            "columns": analyze.columns,
            "quality_score": analyze.quality_score,
            "tags": analyze.semantic_tags,
        },
    )

    # ---- Persist analyze results --------------------------------------------
    async with session_scope() as db:
        res = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
        d = res.scalar_one_or_none()
        if d is None:
            return
        d.rows = analyze.rows
        d.columns = analyze.columns
        d.quality_score = analyze.quality_score
        d.ai_readiness = analyze.ai_readiness
        d.quality_grade = analyze.quality_grade or _grade(analyze.quality_score)
        d.progress = 35

        existing_a = await db.execute(
            select(DatasetAnalytics).where(DatasetAnalytics.dataset_id == dataset_id)
        )
        a = existing_a.scalar_one_or_none()
        if a is None:
            a = DatasetAnalytics(dataset_id=dataset_id)
            db.add(a)
        a.summary = analyze.summary
        a.semantic_tags = analyze.semantic_tags
        a.topics = analyze.topics
        a.quality_metrics = analyze.quality_metrics
        a.duplicate_ratio = analyze.duplicate_ratio
        a.missing_ratio = analyze.missing_ratio
        a.column_profile = analyze.column_profile
        a.sample_rows = analyze.sample_rows

    # ---- Chunk + embed + index ----------------------------------------------
    await _publish(topic, EventType.EMBED_STARTED, {})
    chunks = chunk_file(local_path, format_)
    indexed = await index_chunks(
        dataset_id=dataset_id,
        owner_wallet=owner_wallet,
        title=title,
        category=category,
        tags=tags,
        chunks=chunks,
    )
    await _publish(topic, EventType.EMBED_COMPLETED, {"chunks": indexed})

    async with session_scope() as db:
        res = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
        d = res.scalar_one_or_none()
        if d is not None:
            d.embeddings_count = indexed
            d.progress = 60

    # ---- Push to 0G Storage --------------------------------------------------
    await _publish(topic, EventType.STORAGE_PUSHING, {})
    og_result = await og_client.upload(local_path)

    # Upload a metadata manifest separately so the on-chain `metadataURI`
    # points to the descriptor, not the raw payload.
    manifest = {
        "title": title,
        "description": "",  # filled below from dataset
        "category": category,
        "tags": tags,
        "rows": analyze.rows,
        "columns": analyze.columns,
        "quality_score": analyze.quality_score,
        "semantic_tags": analyze.semantic_tags,
        "summary": analyze.summary,
        "storage_root": og_result["root"],
    }
    manifest_path = local_path.with_suffix(local_path.suffix + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2))
    manifest_result = await og_client.upload(manifest_path)
    metadata_uri = f"0g://{manifest_result['root']}"

    # ---- Persist storage refs ------------------------------------------------
    async with session_scope() as db:
        res = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
        d = res.scalar_one_or_none()
        if d is not None:
            d.storage_root = og_result["root"]
            d.storage_tx_hash = og_result.get("tx_hash")
            d.metadata_uri = metadata_uri
            d.progress = 75

    # ---- Anchor on chain -----------------------------------------------------
    settings = get_settings()
    if settings.web3_user_tx:
        # Hand the chain step to the frontend: the connected wallet will mint
        # the DatasetNFT and call DatasetRegistry.register itself. The dataset
        # parks in PENDING_CHAIN until /datasets/{id}/chain-confirm fires (or
        # the on-chain indexer picks up the events).
        async with session_scope() as db:
            res = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
            d = res.scalar_one_or_none()
            if d is not None:
                d.status = DatasetStatus.PENDING_CHAIN
                d.progress = 85

        await _publish(
            topic,
            EventType.STORAGE_ANCHORED,
            {
                "storage_root": og_result["root"],
                "tx_hash": og_result.get("tx_hash"),
                "metadata_uri": metadata_uri,
                "mode": og_result.get("mode"),
                "pending_chain": True,
                "chain_args": {
                    "storage_root": og_result["root"],
                    "metadata_uri": metadata_uri,
                },
            },
        )
        await _publish(
            topic,
            EventType.UPLOAD_COMPLETED,
            {
                "dataset_id": dataset_id,
                "embeddings": indexed,
                "pending_chain": True,
            },
        )
        return

    # Server-signed (mock or live-with-server-key) — legacy path.
    chain = await chain_registry.register_dataset(
        storage_root=og_result["root"], metadata_uri=metadata_uri
    )

    async with session_scope() as db:
        res = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
        d = res.scalar_one_or_none()
        if d is not None:
            d.chain_id = chain.get("chain_id")
            d.onchain_id = chain.get("onchain_id")
            d.status = DatasetStatus.READY
            d.progress = 100

    await _publish(
        topic,
        EventType.STORAGE_ANCHORED,
        {
            "storage_root": og_result["root"],
            "tx_hash": og_result.get("tx_hash"),
            "chain_tx_hash": chain.get("tx_hash"),
            "onchain_id": chain.get("onchain_id"),
            "metadata_uri": metadata_uri,
            "mode": og_result.get("mode"),
        },
    )
    await _publish(
        topic,
        EventType.UPLOAD_COMPLETED,
        {"dataset_id": dataset_id, "embeddings": indexed},
    )
