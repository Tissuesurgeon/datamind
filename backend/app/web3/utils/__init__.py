"""Hex / address / log decoding helpers for the chain indexer."""

from __future__ import annotations

from typing import Iterable


def ensure_0x(value: str) -> str:
    return value if value.startswith("0x") else f"0x{value}"


def normalize_address(value: str | None) -> str | None:
    if not value:
        return None
    return ensure_0x(value).lower()


def hex_to_int(value: str | bytes | int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, (bytes, bytearray)):
        return int.from_bytes(bytes(value), "big")
    s = ensure_0x(value)
    return int(s, 16)


def topics_match(topics: Iterable[str], expected: str) -> bool:
    return any((t or "").lower() == expected.lower() for t in topics)
