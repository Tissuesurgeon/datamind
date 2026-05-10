"""Shared pagination + envelope schemas."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageInfo(BaseModel):
    total: int
    limit: int
    offset: int

    @property
    def has_more(self) -> bool:
        return self.offset + self.limit < self.total


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: PageInfo


class HealthOut(BaseModel):
    status: str = "ok"
    version: str = Field(default="0.1.0")
    services: dict[str, str] = Field(default_factory=dict)
