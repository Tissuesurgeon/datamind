"""0G Storage client.

Mock-by-default: deterministic fake roots derived from the file's SHA-256.
Live mode shells out to `infra/og-bridge/cli.mjs upload <path>` (ports the
@0glabs/0g-ts-sdk bridge from `frxAi/tools/0g-storage-publish`).

Public surface:
    upload(path)        -> {root, tx_hash, size, mode}
    download(root)      -> Path | None
    warmup()            -> None
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[4]  # backend/app/services/storage → repo
BRIDGE_DIR = REPO_ROOT / "infra" / "og-bridge"
BRIDGE_CLI = BRIDGE_DIR / "cli.mjs"
LOCAL_OG_ROOT = REPO_ROOT / "storage_local" / "og"


# --------------------------------------------------------------------------- #
# Lifecycle                                                                   #
# --------------------------------------------------------------------------- #


async def warmup() -> None:
    """Best-effort sanity log of which storage mode we'll use."""
    settings = get_settings()
    LOCAL_OG_ROOT.mkdir(parents=True, exist_ok=True)
    if settings.storage_live:
        log.info("og.mode", live=True, indexer=settings.og_indexer_rpc)
    else:
        log.info("og.mode", live=False, reason="DATAMIND_OG_MOCK or no key")


# --------------------------------------------------------------------------- #
# Upload                                                                      #
# --------------------------------------------------------------------------- #


def _mock_root(payload: bytes) -> str:
    """Stable, deterministic `0x…` root from the file payload."""
    return "0x" + hashlib.sha256(payload).hexdigest()


def _mock_tx(root: str) -> str:
    return "0x" + hashlib.sha256(("tx::" + root).encode()).hexdigest()


async def upload(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    settings = get_settings()
    if not p.exists():
        raise FileNotFoundError(p)

    if not settings.storage_live or not BRIDGE_CLI.exists():
        # Mock path — copy into local "0G mirror" + emit deterministic root.
        data = p.read_bytes()
        root = _mock_root(data)
        tx = _mock_tx(root)
        target = LOCAL_OG_ROOT / root.removeprefix("0x")
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(data)
        return {
            "root": root,
            "tx_hash": tx,
            "size": len(data),
            "mode": "mock",
        }

    # Live path — shell to node bridge. Bridge prints a single JSON line.
    cmd = [
        "node",
        str(BRIDGE_CLI),
        "upload",
        "--file",
        str(p),
        "--rpc",
        settings.og_evm_rpc,
        "--indexer",
        settings.og_indexer_rpc,
    ]
    if settings.og_private_key is not None:
        cmd += ["--key", settings.og_private_key.get_secret_value()]

    log.info("og.upload.live", path=str(p))
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(REPO_ROOT),
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        log.warning(
            "og.upload.live.failed", code=proc.returncode, err=stderr.decode("utf-8", "ignore")
        )
        # Fall back to deterministic mock so the demo never breaks.
        data = p.read_bytes()
        return {
            "root": _mock_root(data),
            "tx_hash": _mock_tx(_mock_root(data)),
            "size": len(data),
            "mode": "mock-fallback",
            "error": stderr.decode("utf-8", "ignore")[-512:],
        }

    line = (stdout.decode("utf-8", "ignore").splitlines() or [""])[-1]
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        log.warning("og.upload.bad-json", out=line)
        data = {"root": _mock_root(p.read_bytes()), "tx_hash": "", "size": p.stat().st_size}
    data.setdefault("mode", "live")
    return data


# --------------------------------------------------------------------------- #
# Download                                                                    #
# --------------------------------------------------------------------------- #


async def download(root: str) -> Path | None:
    """Return a local path to the file with the given storage root.

    In mock mode this just returns the file we mirrored on upload.
    Live mode would shell to the bridge's `download` subcommand (TODO: wire when
    the bridge implements it; for now we mirror to avoid breaking demos).
    """
    settings = get_settings()
    target = LOCAL_OG_ROOT / root.removeprefix("0x")
    if target.exists():
        return target

    if not settings.storage_live or not BRIDGE_CLI.exists():
        return None

    log.info("og.download.live", root=root)
    cmd = [
        "node",
        str(BRIDGE_CLI),
        "download",
        "--root",
        root,
        "--out",
        str(target),
        "--indexer",
        settings.og_indexer_rpc,
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        log.warning("og.download.live.failed", err=stderr.decode("utf-8", "ignore"))
        return None
    return target if target.exists() else None
