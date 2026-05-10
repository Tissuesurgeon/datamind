"""Marketplace endpoints — public, no auth required."""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload

from app.core.deps import DBSession
from app.models.dataset import Dataset, DatasetStatus, DatasetVisibility
from app.schemas.common import Page, PageInfo
from app.schemas.dataset import DatasetMarketplaceItem

router = APIRouter()


def _to_market(d: Dataset) -> DatasetMarketplaceItem:
    return DatasetMarketplaceItem(
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
        price_amount=d.price_amount,
        price_token=d.price_token,
        license_kind=d.license_kind,
    )


@router.get("", response_model=Page[DatasetMarketplaceItem])
async def marketplace(
    db: DBSession,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: str | None = None,
    sort: str = Query("trending", pattern="^(trending|recent|quality|downloads)$"),
) -> Page[DatasetMarketplaceItem]:
    stmt = (
        select(Dataset)
        .options(selectinload(Dataset.owner))
        .where(
            Dataset.visibility == DatasetVisibility.PUBLIC,
            Dataset.status == DatasetStatus.READY,
        )
    )
    if category and category.lower() != "all":
        stmt = stmt.where(Dataset.category == category)

    if sort == "recent":
        stmt = stmt.order_by(desc(Dataset.created_at))
    elif sort == "quality":
        stmt = stmt.order_by(desc(Dataset.quality_score))
    elif sort == "downloads":
        stmt = stmt.order_by(desc(Dataset.downloads))
    else:  # trending: weighted combination
        stmt = stmt.order_by(
            desc(Dataset.downloads + Dataset.views * 0.1),
            desc(Dataset.created_at),
        )

    total_rows = (await db.execute(stmt.with_only_columns(Dataset.id))).all()
    res = await db.execute(stmt.offset(offset).limit(limit))
    return Page(
        items=[_to_market(d) for d in res.scalars().all()],
        page=PageInfo(total=len(total_rows), limit=limit, offset=offset),
    )


@router.get("/trending", response_model=list[DatasetMarketplaceItem])
async def trending(db: DBSession, limit: int = Query(6, ge=1, le=20)) -> list[DatasetMarketplaceItem]:
    res = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.owner))
        .where(
            Dataset.visibility == DatasetVisibility.PUBLIC,
            Dataset.status == DatasetStatus.READY,
        )
        .order_by(desc(Dataset.downloads + Dataset.views * 0.1), desc(Dataset.created_at))
        .limit(limit)
    )
    return [_to_market(d) for d in res.scalars().all()]
