"""Dataset + DatasetFile models."""

from __future__ import annotations

import enum

from sqlalchemy import (
    JSON,
    BigInteger,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin


class DatasetVisibility(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"


class DatasetStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    PENDING_CHAIN = "pending_chain"
    READY = "ready"
    FAILED = "failed"


class Dataset(IdMixin, TimestampMixin, Base):
    __tablename__ = "datasets"

    owner_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    # File-level info
    format: Mapped[str] = mapped_column(String(16), nullable=False)  # csv|json|txt|pdf
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    columns: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Quality + AI metadata
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_readiness: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_grade: Mapped[str | None] = mapped_column(String(2), nullable=True)  # A|B|C
    embeddings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 0G + chain
    storage_root: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    storage_tx_hash: Mapped[str | None] = mapped_column(String(80), nullable=True)
    chain_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    onchain_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_uri: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Lifecycle
    visibility: Mapped[DatasetVisibility] = mapped_column(
        SAEnum(
            DatasetVisibility,
            name="dataset_visibility",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=DatasetVisibility.PUBLIC,
        nullable=False,
    )
    status: Mapped[DatasetStatus] = mapped_column(
        SAEnum(
            DatasetStatus,
            name="dataset_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=DatasetStatus.UPLOADING,
        nullable=False,
    )
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0-100

    # Marketplace
    price_token: Mapped[str | None] = mapped_column(String(16), nullable=True)
    price_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    license_kind: Mapped[str | None] = mapped_column(String(32), nullable=True)
    downloads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relations
    owner: Mapped["User"] = relationship("User", back_populates="datasets")  # noqa: F821
    files: Mapped[list["DatasetFile"]] = relationship(
        "DatasetFile",
        back_populates="dataset",
        cascade="all,delete-orphan",
    )
    embeddings: Mapped[list["DatasetEmbedding"]] = relationship(  # noqa: F821
        "DatasetEmbedding",
        back_populates="dataset",
        cascade="all,delete-orphan",
    )
    analytics: Mapped["DatasetAnalytics | None"] = relationship(  # noqa: F821
        "DatasetAnalytics",
        back_populates="dataset",
        uselist=False,
        cascade="all,delete-orphan",
    )
    nft: Mapped["DatasetNFT | None"] = relationship(  # noqa: F821
        "DatasetNFT",
        back_populates="dataset",
        uselist=False,
        cascade="all,delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Dataset id={self.id} title={self.title!r} status={self.status}>"


class DatasetFile(IdMixin, TimestampMixin, Base):
    __tablename__ = "dataset_files"

    dataset_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("datasets.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    local_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    storage_root: Mapped[str | None] = mapped_column(String(80), nullable=True)

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="files")
