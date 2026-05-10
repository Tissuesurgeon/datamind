"""SQLAlchemy declarative base + shared mixins."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _ulid() -> str:
    """Time-ordered unique id, stored as a 26-char string for readability."""
    import ulid
    return str(ulid.new())


class Base(DeclarativeBase):
    pass


class IdMixin:
    """Adds a 26-char ULID primary key called `id`."""

    id: Mapped[str] = mapped_column(
        String(26),
        primary_key=True,
        default=_ulid,
        nullable=False,
    )


class TimestampMixin:
    """Adds `created_at` / `updated_at` UTC timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


def new_id() -> str:
    return _ulid()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# Convenience UUID helper used by the migrations + scripts.
def new_uuid() -> str:
    return str(uuid.uuid4())
