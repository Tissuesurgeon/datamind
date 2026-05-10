"""ID helpers used across the codebase."""

from __future__ import annotations

import secrets

import ulid


def new_ulid() -> str:
    return str(ulid.new())


def short_token(nbytes: int = 12) -> str:
    return secrets.token_urlsafe(nbytes)
