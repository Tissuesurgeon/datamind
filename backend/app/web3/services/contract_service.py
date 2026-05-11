"""Read-side contract helpers using `web3.py`.

Each helper degrades gracefully when contracts are not configured (mock mode):
they return `None` rather than raising so callers can fall back to local DB
state.
"""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger
from app.web3.contracts import load_abi

log = get_logger(__name__)


def is_chain_configured() -> bool:
    s = get_settings()
    return bool(
        s.dataset_registry_address
        and s.og_evm_rpc
    )


def _web3():
    s = get_settings()
    try:
        from web3 import AsyncWeb3
        from web3.providers.async_rpc import AsyncHTTPProvider
        return AsyncWeb3(AsyncHTTPProvider(s.og_evm_rpc))
    except Exception as exc:  # pragma: no cover
        log.warning("web3.init.failed", error=str(exc))
        return None


def get_contract(contract_name: str, address: str | None):
    if not address:
        return None
    w3 = _web3()
    if w3 is None:
        return None
    abi = load_abi(contract_name)
    if abi is None:
        log.warning("web3.abi.missing", contract=contract_name)
        return None
    try:
        return w3, w3.eth.contract(address=address, abi=abi)
    except Exception as exc:  # pragma: no cover
        log.warning("web3.contract.failed", contract=contract_name, error=str(exc))
        return None


async def read_dataset_owner(onchain_id: int) -> str | None:
    s = get_settings()
    ctx = get_contract("DatasetRegistry", s.dataset_registry_address)
    if ctx is None:
        return None
    _, contract = ctx
    try:
        return await contract.functions.ownerOf(onchain_id).call()
    except Exception as exc:
        log.warning("web3.read.ownerOf.failed", id=onchain_id, error=str(exc))
        return None


async def read_nft_owner(token_id: int) -> str | None:
    s = get_settings()
    ctx = get_contract("DatasetNFT", s.dataset_nft_address)
    if ctx is None:
        return None
    _, contract = ctx
    try:
        return await contract.functions.ownerOf(token_id).call()
    except Exception as exc:
        log.warning("web3.read.nft.ownerOf.failed", token=token_id, error=str(exc))
        return None


async def read_training_job(job_id: int) -> dict[str, Any] | None:
    s = get_settings()
    ctx = get_contract("TrainingRegistry", s.training_registry_address)
    if ctx is None:
        return None
    _, contract = ctx
    try:
        raw = await contract.functions.getJob(job_id).call()
        # The struct returns a tuple — surface a friendlier dict shape.
        return {
            "id":             raw[0],
            "datasetId":      raw[1],
            "operator":       raw[2],
            "baseModel":      raw[3],
            "configURI":      raw[4],
            "checkpointRoot": "0x" + raw[5].hex() if isinstance(raw[5], (bytes, bytearray)) else raw[5],
            "status":         raw[6],
            "createdAt":      raw[7],
            "updatedAt":      raw[8],
            "exists":         raw[9],
        }
    except Exception as exc:
        log.warning("web3.read.getJob.failed", id=job_id, error=str(exc))
        return None
