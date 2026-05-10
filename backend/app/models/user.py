"""User model — keyed by wallet address (Privy or mock)."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin


class User(IdMixin, TimestampMixin, Base):
    __tablename__ = "users"

    wallet_address: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    datasets: Mapped[list["Dataset"]] = relationship(  # noqa: F821
        "Dataset", back_populates="owner", cascade="all,delete-orphan"
    )
    training_jobs: Mapped[list["TrainingJob"]] = relationship(  # noqa: F821
        "TrainingJob", back_populates="owner", cascade="all,delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} wallet={self.wallet_address}>"
