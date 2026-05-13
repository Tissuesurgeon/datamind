"""0G Storage client.

Mock-by-default: fake roots from SHA-256(file + optional salt). The salt avoids
`DatasetAlreadyRegistered` on-chain when the same bytes are uploaded again (common
in demos). Live mode ignores the salt.
Live mode shells out to `infra/og-bridge/cli.mjs upload <path>` using
`@0gfoundation/0g-storage-ts-sdk` (see https://build.0g.ai/storage/).

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
        if not BRIDGE_CLI.exists():
            log.warning(
                "og.bridge.missing",
                expected=str(BRIDGE_CLI),
                hint="Rebuild backend image with infra/og-bridge + Node or use DATAMIND_OG_MOCK=1",
            )
        log.info("og.mode", live=True, indexer=settings.og_indexer_rpc, bridge=str(BRIDGE_CLI))
    else:
        log.info("og.mode", live=False, reason="DATAMIND_OG_MOCK or no key")


# --------------------------------------------------------------------------- #
# Upload                                                                      #
# --------------------------------------------------------------------------- #


def _mock_root(payload: bytes, salt: str | None = None) -> str:
    """Deterministic `0x…` root from file bytes, optionally namespaced by *salt*."""
    h = hashlib.sha256()
    h.update(payload)
    if salt:
        h.update(b"\x00")
        h.update(salt.encode("utf-8"))
    return "0x" + h.hexdigest()


def _mock_tx(root: str) -> str:
    return "0x" + hashlib.sha256(("tx::" + root).encode()).hexdigest()


async def upload(path: str | Path, *, dedupe_salt: str | None = None) -> dict[str, Any]:
    # Absolute path required: bridge runs with cwd=REPO_ROOT (/app); uploads often live
    # under /app/backend/storage_local when BACKEND_UPLOAD_DIR is relative.
    p = Path(path).resolve()
    settings = get_settings()
    if not p.exists():
        raise FileNotFoundError(p)

    if not settings.storage_live:
        # Mock path — copy into local "0G mirror" + emit deterministic root.
        data = p.read_bytes()
        root = _mock_root(data, dedupe_salt)
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

    if not BRIDGE_CLI.exists():
        log.error("og.bridge.missing", path=str(BRIDGE_CLI))
        raise RuntimeError(
            "Live 0G Storage is enabled (DATAMIND_OG_MOCK=0 with OG_PRIVATE_KEY) but "
            f"the Node bridge is missing at {BRIDGE_CLI}. Rebuild the backend Docker "
            "image so it includes infra/og-bridge and Node.js, or set DATAMIND_OG_MOCK=1."
        )

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
    err_txt = stderr.decode("utf-8", "ignore")
    out_txt = stdout.decode("utf-8", "ignore")
    if proc.returncode != 0:
        detail = err_txt.strip() or out_txt.strip() or "no output"
        log.warning(
            "og.upload.live.failed",
            code=proc.returncode,
            err=err_txt[:2000],
            out=out_txt[:2000],
        )
        raise RuntimeError(
            f"0G bridge upload failed (exit {proc.returncode}): {detail}"
        )

    line = (stdout.decode("utf-8", "ignore").splitlines() or [""])[-1]
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        log.warning("og.upload.bad-json", out=line[:500])
        raise RuntimeError(f"0G bridge did not return JSON: {line[:500]!r}") from None

    mode = data.get("mode")
    if mode != "live":
        detail = data.get("reason") or data.get("error") or line
        raise RuntimeError(
            f"0G Storage upload was not live (mode={mode!r}): {detail}. "
            "If you intended live uploads: fund the server wallet (e.g. https://faucet.0g.ai), "
            "set OG_EVM_RPC to https://evmrpc-testnet.0g.ai and OG_INDEXER_RPC to the turbo "
            "testnet indexer from https://build.0g.ai/storage/, then redeploy the backend "
            "image so /app/infra/og-bridge uses @0gfoundation/0g-storage-ts-sdk."
        )
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

    if not settings.storage_live:
        return None

    if not BRIDGE_CLI.exists():
        log.warning("og.download.bridge.missing", path=str(BRIDGE_CLI))
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
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        err = stderr.decode("utf-8", "ignore").strip()
        out = stdout.decode("utf-8", "ignore").strip()
        log.warning(
            "og.download.live.failed",
            err=err[:1500],
            out=out[:1500],
        )
        return None
    return target if target.exists() else None
