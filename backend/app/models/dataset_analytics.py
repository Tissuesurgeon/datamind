"""DatasetAnalytics — AI-generated summary, tags, quality breakdown."""

from __future__ import annotations

from sqlalchemy import JSON, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin


class DatasetAnalytics(IdMixin, TimestampMixin, Base):
    __tablename__ = "dataset_analytics"

    dataset_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    semantic_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    topics: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    quality_metrics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    duplicate_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    missing_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    column_profile: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    sample_rows: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)

    dataset: Mapped["Dataset"] = relationship(  # noqa: F821
        "Dataset", back_populates="analytics"
    )
