"""Cross-cutting hashing helpers."""

from __future__ import annotations

import hashlib

from eth_utils import keccak, to_hex


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def keccak256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return to_hex(keccak(data))
