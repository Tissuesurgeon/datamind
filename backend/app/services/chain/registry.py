"""DatasetRegistry chain client.

Mock-by-default: keeps an in-memory registry keyed by (storage_root → onchain_id).
Live mode uses `web3.py` against the deployed `DatasetRegistry.sol` on Galileo.

Public API:
    register_dataset(storage_root, metadata_uri) -> {onchain_id, tx_hash, mode}
"""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger
from app.web3.contracts import load_abi as _load_abi_v2

log = get_logger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[4]
ABI_PATH = REPO_ROOT / "smart-contracts" / "out" / "DatasetRegistry.sol" / "DatasetRegistry.json"


_in_memory_seq = itertools.count(1)
_in_memory: dict[str, dict[str, Any]] = {}


def _mock_tx(payload: str) -> str:
    return "0x" + hashlib.sha256(payload.encode()).hexdigest()


# --------------------------------------------------------------------------- #
# Web3 helpers                                                                #
# --------------------------------------------------------------------------- #


def _load_abi() -> list[dict] | None:
    # Delegate to the canonical loader in `app.web3.contracts` so we don't keep
    # two copies of the same path glue. Falls back to the historical literal
    # path for backwards compatibility with existing tooling.
    abi = _load_abi_v2("DatasetRegistry")
    if abi is not None:
        return abi
    if not ABI_PATH.exists():
        return None
    try:
        data = json.loads(ABI_PATH.read_text())
        return data.get("abi")
    except Exception as exc:  # pragma: no cover
        log.warning("chain.abi.load.failed", error=str(exc))
        return None


def _w3_and_contract():
    settings = get_settings()
    if not settings.chain_live:
        return None, None
    abi = _load_abi()
    if abi is None:
        log.warning("chain.abi.missing", path=str(ABI_PATH))
        return None, None
    try:
        from web3 import AsyncWeb3
        from web3.providers.async_rpc import AsyncHTTPProvider

        w3 = AsyncWeb3(AsyncHTTPProvider(settings.og_evm_rpc))
        contract = w3.eth.contract(
            address=settings.dataset_registry_address, abi=abi
        )
        return w3, contract
    except Exception as exc:  # pragma: no cover
        log.warning("chain.w3.init.failed", error=str(exc))
        return None, None


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #


async def register_dataset(*, storage_root: str, metadata_uri: str) -> dict[str, Any]:
    """Register a dataset on-chain (or mock).

    Returns:
        {onchain_id: int, tx_hash: str, chain_id: int, mode: 'live'|'mock'}
    """
    settings = get_settings()

    # Already registered? (idempotent for the demo flow).
    if storage_root in _in_memory:
        existing = _in_memory[storage_root]
        return {**existing, "mode": existing.get("mode", "mock")}

    if settings.chain_live:
        w3, contract = _w3_and_contract()
        if w3 is None or contract is None:
            log.warning("chain.live.fallback", reason="contract unavailable")
        else:
            try:
                from eth_account import Account

                acct = Account.from_key(settings.og_private_key.get_secret_value())  # type: ignore[union-attr]
                # Build, sign, send.
                root_bytes = bytes.fromhex(storage_root.removeprefix("0x"))[:32].rjust(32, b"\x00")
                func = contract.functions.register(root_bytes, metadata_uri)
                nonce = await w3.eth.get_transaction_count(acct.address)
                gas = await func.estimate_gas({"from": acct.address})
                tx = await func.build_transaction(
                    {
                        "from": acct.address,
                        "nonce": nonce,
                        "gas": int(gas * 1.2),
                        "gasPrice": await w3.eth.gas_price,
                        "chainId": settings.og_chain_id,
                    }
                )
                signed = acct.sign_transaction(tx)
                tx_hash = await w3.eth.send_raw_transaction(signed.raw_transaction)
                receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
                # Decode `DatasetRegistered` event for the new id.
                onchain_id = 0
                for ev in contract.events.DatasetRegistered().process_receipt(receipt):
                    onchain_id = int(ev["args"]["id"])
                    break
                result = {
                    "onchain_id": onchain_id,
                    "tx_hash": "0x" + tx_hash.hex(),
                    "chain_id": settings.og_chain_id,
                    "mode": "live",
                }
                _in_memory[storage_root] = result
                return result
            except Exception as exc:
                log.warning("chain.register.live.failed", error=str(exc))

    # Mock path
    onchain_id = next(_in_memory_seq)
    tx_hash = _mock_tx(f"register::{storage_root}::{metadata_uri}")
    result = {
        "onchain_id": onchain_id,
        "tx_hash": tx_hash,
        "chain_id": settings.og_chain_id,
        "mode": "mock",
    }
    _in_memory[storage_root] = result
    return result


async def get_provenance(storage_root: str) -> dict[str, Any] | None:
    return _in_memory.get(storage_root)
