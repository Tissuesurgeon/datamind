"""Dataset CRUD + upload pipeline trigger."""

from __future__ import annotations

import json

from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DBSession, OptionalUser
from app.models.dataset import Dataset, DatasetStatus, DatasetVisibility
from app.models.dataset_analytics import DatasetAnalytics
from app.schemas.common import Page, PageInfo
from app.schemas.dataset import (
    DatasetDetail,
    DatasetListItem,
    DatasetSummary,
    DatasetUpdate,
    DatasetUploadResponse,
)
from app.services.datasets.ingest import ingest_dataset, run_pipeline_in_background
from app.utils.files import save_upload, sniff_format, guess_mime

router = APIRouter()


def _to_summary(d: Dataset) -> DatasetSummary:
    return DatasetSummary(
        id=d.id,
        title=d.title,
        category=d.category,
        tags=list(d.tags or []),
        quality_score=d.quality_score,
        quality_grade=d.quality_grade,
        ai_readiness=d.ai_readiness,
        rows=d.rows,
        embeddings_count=d.embeddings_count,
        downloads=d.downloads,
        visibility=d.visibility.value,
        status=d.status.value,
        progress=d.progress,
        storage_root=d.storage_root,
        onchain_id=d.onchain_id,
        owner_wallet=d.owner.wallet_address if d.owner else "",
        created_at=d.created_at,
    )


def _to_detail(d: Dataset, a: DatasetAnalytics | None) -> DatasetDetail:
    return DatasetDetail(
        id=d.id,
        title=d.title,
        category=d.category,
        tags=list(d.tags or []),
        quality_score=d.quality_score,
        quality_grade=d.quality_grade,
        ai_readiness=d.ai_readiness,
        rows=d.rows,
        embeddings_count=d.embeddings_count,
        downloads=d.downloads,
        visibility=d.visibility.value,
        status=d.status.value,
        progress=d.progress,
        storage_root=d.storage_root,
        onchain_id=d.onchain_id,
        owner_wallet=d.owner.wallet_address if d.owner else "",
        created_at=d.created_at,
        description=d.description,
        format=d.format,
        size_bytes=d.size_bytes,
        columns=d.columns,
        storage_tx_hash=d.storage_tx_hash,
        metadata_uri=d.metadata_uri,
        license_kind=d.license_kind,
        price_amount=d.price_amount,
        price_token=d.price_token,
        summary=a.summary if a else None,
        semantic_tags=list(a.semantic_tags) if a else [],
        topics=list(a.topics) if a else [],
        quality_metrics=dict(a.quality_metrics) if a else {},
        sample_rows=list(a.sample_rows) if a else [],
    )


@router.post("", response_model=DatasetUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    user: CurrentUser,
    db: DBSession,
    background: BackgroundTasks,
    file: UploadFile,
    title: str = Form(...),
    description: str | None = Form(None),
    category: str = Form("Other"),
    tags: str = Form("[]"),
    visibility: str = Form("public"),
    price_amount: float | None = Form(None),
    license_kind: str | None = Form(None),
) -> DatasetUploadResponse:
    """Multipart upload + register a new dataset; queues the AI pipeline."""
    try:
        tag_list = json.loads(tags) if tags else []
        if not isinstance(tag_list, list):
            tag_list = []
    except json.JSONDecodeError:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    dataset = Dataset(
        owner_id=user.id,
        title=title,
        description=description,
        category=category,
        tags=tag_list,
        format=sniff_format(file.filename or ""),
        visibility=DatasetVisibility(visibility),
        status=DatasetStatus.UPLOADING,
        price_amount=price_amount,
        price_token="OG",
        license_kind=license_kind,
    )
    db.add(dataset)
    await db.flush()

    path, sha256, size = await save_upload(file, dataset.id)
    mime = guess_mime(file.filename or "")
    await ingest_dataset(
        db,
        dataset=dataset,
        local_path=path,
        sha256=sha256,
        size=size,
        mime=mime,
        original_filename=file.filename or "uploaded.bin",
    )
    await db.flush()
    await db.refresh(dataset, attribute_names=["owner"])

    summary = _to_summary(dataset)
    ws_topic = f"dataset:{dataset.id}"

    # Process the pipeline asynchronously after the response is returned.
    background.add_task(run_pipeline_in_background, dataset.id)

    return DatasetUploadResponse(dataset=summary, ws_topic=ws_topic)


@router.get("", response_model=Page[DatasetListItem])
async def list_datasets(
    db: DBSession,
    user: OptionalUser,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    mine: bool = False,
    category: str | None = None,
    visibility: str | None = None,
) -> Page[DatasetListItem]:
    stmt = select(Dataset).options(selectinload(Dataset.owner)).order_by(desc(Dataset.created_at))
    if mine:
        if user is None:
            raise HTTPException(status_code=401, detail="login required for ?mine=true")
        stmt = stmt.where(Dataset.owner_id == user.id)
    else:
        stmt = stmt.where(Dataset.visibility == DatasetVisibility.PUBLIC)
    if category:
        stmt = stmt.where(Dataset.category == category)
    if visibility:
        stmt = stmt.where(Dataset.visibility == DatasetVisibility(visibility))

    total = (await db.execute(stmt.with_only_columns(Dataset.id))).all()
    items_res = await db.execute(stmt.offset(offset).limit(limit))
    items = items_res.scalars().all()
    return Page(
        items=[_to_summary(d) for d in items],
        page=PageInfo(total=len(total), limit=limit, offset=offset),
    )


@router.get("/{dataset_id}", response_model=DatasetDetail)
async def get_dataset(dataset_id: str, db: DBSession) -> DatasetDetail:
    res = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.owner), selectinload(Dataset.analytics))
        .where(Dataset.id == dataset_id)
    )
    d = res.scalar_one_or_none()
    if d is None:
        raise HTTPException(status_code=404, detail="dataset not found")
    return _to_detail(d, d.analytics)


@router.patch("/{dataset_id}", response_model=DatasetDetail)
async def update_dataset(
    dataset_id: str,
    payload: DatasetUpdate,
    user: CurrentUser,
    db: DBSession,
) -> DatasetDetail:
    res = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.owner), selectinload(Dataset.analytics))
        .where(Dataset.id == dataset_id)
    )
    d = res.scalar_one_or_none()
    if d is None:
        raise HTTPException(status_code=404, detail="dataset not found")
    if d.owner_id != user.id:
        raise HTTPException(status_code=403, detail="forbidden")

    for field, value in payload.model_dump(exclude_none=True).items():
        if field == "visibility":
            d.visibility = DatasetVisibility(value)
        else:
            setattr(d, field, value)
    await db.flush()
    await db.refresh(d)
    return _to_detail(d, d.analytics)


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_dataset(dataset_id: str, user: CurrentUser, db: DBSession) -> Response:
    res = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    d = res.scalar_one_or_none()
    if d is None:
        raise HTTPException(status_code=404, detail="dataset not found")
    if d.owner_id != user.id:
        raise HTTPException(status_code=403, detail="forbidden")
    await db.delete(d)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
