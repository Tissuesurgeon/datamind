"""DatasetLicense — local mirror of on-chain license grants."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class LicenseKind(str, enum.Enum):
    PERSONAL = "personal"
    COMMERCIAL = "commercial"
    ACADEMIC = "academic"
    EXCLUSIVE = "exclusive"


class DatasetLicense(IdMixin, TimestampMixin, Base):
    __tablename__ = "dataset_licenses"

    dataset_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("datasets.id", ondelete="CASCADE"), index=True
    )
    grantee_wallet: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    kind: Mapped[LicenseKind] = mapped_column(
        SAEnum(LicenseKind, name="license_kind"),
        default=LicenseKind.PERSONAL,
        nullable=False,
    )
    onchain_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    tx_hash: Mapped[str | None] = mapped_column(String(80), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked: Mapped[bool] = mapped_column(default=False, nullable=False)
