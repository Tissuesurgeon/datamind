"""LicenseRegistry chain client (mock-first)."""

from __future__ import annotations

import hashlib
import itertools
from datetime import datetime, timezone
from typing import Any

_seq = itertools.count(1)
_in_memory: list[dict[str, Any]] = []


def _mock_tx(payload: str) -> str:
    return "0x" + hashlib.sha256(payload.encode()).hexdigest()


async def mint_license(
    *,
    dataset_onchain_id: int,
    grantee_wallet: str,
    kind: str = "personal",
    expires_at: datetime | None = None,
) -> dict[str, Any]:
    license_id = next(_seq)
    record = {
        "onchain_id": license_id,
        "dataset_onchain_id": dataset_onchain_id,
        "grantee_wallet": grantee_wallet.lower(),
        "kind": kind,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "minted_at": datetime.now(tz=timezone.utc).isoformat(),
        "tx_hash": _mock_tx(f"license::{license_id}::{grantee_wallet}"),
        "revoked": False,
        "mode": "mock",
    }
    _in_memory.append(record)
    return record


async def list_licenses(dataset_onchain_id: int | None = None) -> list[dict[str, Any]]:
    if dataset_onchain_id is None:
        return list(_in_memory)
    return [r for r in _in_memory if r["dataset_onchain_id"] == dataset_onchain_id]
