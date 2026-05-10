"""DatasetEmbedding — one row per chunk vector indexed in Qdrant."""

from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin


class DatasetEmbedding(IdMixin, TimestampMixin, Base):
    __tablename__ = "dataset_embeddings"

    dataset_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("datasets.id", ondelete="CASCADE"), index=True
    )
    vector_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)

    dataset: Mapped["Dataset"] = relationship(  # noqa: F821
        "Dataset", back_populates="embeddings"
    )
