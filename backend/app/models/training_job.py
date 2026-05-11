"""TrainingJob — LoRA fine-tuning runs."""

from __future__ import annotations

import enum

from sqlalchemy import JSON, Enum as SAEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin


class TrainingJobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrainingJob(IdMixin, TimestampMixin, Base):
    __tablename__ = "training_jobs"

    user_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    dataset_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("datasets.id", ondelete="CASCADE"), index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_model: Mapped[str] = mapped_column(String(128), nullable=False)
    task: Mapped[str] = mapped_column(String(64), nullable=False, default="causal_lm")
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    status: Mapped[TrainingJobStatus] = mapped_column(
        SAEnum(
            TrainingJobStatus,
            name="training_job_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=TrainingJobStatus.PENDING,
        nullable=False,
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    epoch: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    checkpoint_root: Mapped[str | None] = mapped_column(String(80), nullable=True)
    checkpoint_tx_hash: Mapped[str | None] = mapped_column(String(80), nullable=True)

    owner: Mapped["User"] = relationship("User", back_populates="training_jobs")  # noqa: F821
