"""Foundry-output ABI loader.

`smart-contracts/out/<Name>.sol/<Name>.json` is the canonical artifact. We avoid
hard-coding ABIs here so a fresh `forge build` automatically refreshes signatures.
"""

from __future__ import annotations

import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_FORGE_OUT = _REPO_ROOT / "smart-contracts" / "out"


def load_abi(contract_name: str) -> list[dict] | None:
    """Read an ABI from the Foundry output. Returns `None` if Forge has not
    built yet — callers should degrade gracefully in that case (mock mode)."""
    path = _FORGE_OUT / f"{contract_name}.sol" / f"{contract_name}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        abi = data.get("abi")
        return abi if isinstance(abi, list) else None
    except Exception:
        return None
