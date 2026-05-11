"""Chain log indexer — polls eth_getLogs and mirrors events to Postgres + WS.

The indexer runs in-process as an asyncio task started during FastAPI's
`lifespan`. It listens for:

    DatasetRegistry.DatasetRegistered
    DatasetNFT.DatasetMinted   (+ ERC-721 Transfer for ownership tracking)
    TrainingRegistry.TrainingStarted / TrainingUpdated / TrainingCompleted

Each event is upserted via `_apply_*` handlers, then re-broadcast on the
shared `WebSocketManager.publish` channel so the frontend updates without a
round-trip to wagmi.

Mock-friendly: when chain settings are missing or web3.py fails to connect,
the indexer no-ops instead of crashing the API.
"""

from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import session_scope
from app.models.blockchain_tx import (
    BlockchainActionType,
    BlockchainTransaction,
    BlockchainTxStatus,
)
from app.models.dataset import Dataset, DatasetStatus
from app.models.dataset_nft import DatasetNFT
from app.models.training_job import TrainingJob, TrainingJobStatus
from app.services.realtime import EventType, RealtimeEvent, get_ws_manager
from app.web3.contracts import load_abi

log = get_logger(__name__)


# ---- Topic signatures (computed lazily after we have the ABI) ----------- #


def _event_topic(w3, abi: list[dict], name: str) -> str | None:
    for entry in abi:
        if entry.get("type") == "event" and entry.get("name") == name:
            inputs = entry.get("inputs", [])
            sig = f"{name}({','.join(i['type'] for i in inputs)})"
            return w3.keccak(text=sig).hex()
    return None


class ChainIndexer:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._started = False
        self._last_block: int | None = None

    # ---- lifecycle ----------------------------------------------------------

    async def start(self) -> None:
        if self._started:
            return
        settings = get_settings()
        if not settings.chain_indexer_enabled:
            log.info("chain_indexer.disabled")
            return
        if not settings.dataset_registry_address:
            log.warning("chain_indexer.skip", reason="no DATASET_REGISTRY_ADDRESS")
            return
        self._started = True
        self._stop.clear()
        self._task = asyncio.create_task(self._run(), name="datamind.chain_indexer")
        log.info("chain_indexer.started")

    async def shutdown(self) -> None:
        if not self._started:
            return
        self._stop.set()
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None
        self._started = False
        log.info("chain_indexer.stopped")

    # ---- core loop ----------------------------------------------------------

    async def _run(self) -> None:
        settings = get_settings()
        try:
            from web3 import AsyncWeb3
            from web3.providers.async_rpc import AsyncHTTPProvider
        except Exception as exc:
            log.warning("chain_indexer.web3.missing", error=str(exc))
            return

        w3 = AsyncWeb3(AsyncHTTPProvider(settings.og_evm_rpc))
        try:
            tip = await w3.eth.block_number
            self._last_block = max(
                int(tip) - 1, int(settings.chain_indexer_start_block)
            )
        except Exception as exc:
            log.warning("chain_indexer.rpc.failed", error=str(exc))
            return

        # Resolve ABIs + topic signatures up front.
        topics = _build_topic_index(w3)
        if not topics:
            log.warning("chain_indexer.abi.missing", hint="run forge build")
            return

        poll = max(0.5, settings.chain_indexer_poll_seconds)
        while not self._stop.is_set():
            try:
                tip = int(await w3.eth.block_number)
                if self._last_block is not None and tip > self._last_block:
                    await self._scan_range(w3, topics, self._last_block + 1, tip)
                    self._last_block = tip
            except Exception as exc:  # pragma: no cover
                log.warning("chain_indexer.tick.failed", error=str(exc))
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=poll)
            except asyncio.TimeoutError:
                continue

    async def _scan_range(self, w3, topics: dict[str, Any], from_block: int, to_block: int) -> None:
        s = get_settings()
        addresses = [
            a for a in (
                s.dataset_registry_address,
                s.dataset_nft_address,
                s.training_registry_address,
            ) if a
        ]
        if not addresses:
            return
        # eth_getLogs with no topic filter — cheap on a hackathon-scale testnet.
        try:
            logs = await w3.eth.get_logs(
                {"fromBlock": from_block, "toBlock": to_block, "address": addresses}
            )
        except Exception as exc:
            log.warning("chain_indexer.get_logs.failed", error=str(exc))
            return

        for entry in logs:
            await self._dispatch(entry, topics)

    async def _dispatch(self, entry: dict[str, Any], topics: dict[str, Any]) -> None:
        try:
            log_topic0 = entry["topics"][0].hex() if hasattr(entry["topics"][0], "hex") else entry["topics"][0]
        except Exception:
            return

        handlers = {
            topics["DatasetRegistered"]: self._on_dataset_registered,
            topics["DatasetMinted"]: self._on_dataset_minted,
            topics["TrainingStarted"]: self._on_training_started,
            topics["TrainingUpdated"]: self._on_training_updated,
            topics["TrainingCompleted"]: self._on_training_completed,
        }
        handler = handlers.get(log_topic0)
        if handler is None:
            return
        try:
            await handler(entry)
        except Exception as exc:  # pragma: no cover
            log.warning("chain_indexer.handler.failed", topic=log_topic0, error=str(exc))

    # ---- handlers -----------------------------------------------------------

    async def _on_dataset_registered(self, entry: dict[str, Any]) -> None:
        # indexed: id, owner, storageRoot
        topics_ = [t.hex() if hasattr(t, "hex") else t for t in entry["topics"]]
        onchain_id = int(topics_[1], 16)
        storage_root = topics_[3]
        tx_hash = entry["transactionHash"].hex() if hasattr(entry["transactionHash"], "hex") else entry["transactionHash"]
        block_number = int(entry.get("blockNumber") or 0)

        async with session_scope() as db:
            res = await db.execute(select(Dataset).where(Dataset.storage_root == storage_root))
            dataset = res.scalar_one_or_none()
            if dataset is None:
                # Index orphan tx for forensic visibility.
                await _record_tx(
                    db,
                    tx_hash=tx_hash,
                    action=BlockchainActionType.DATASET_REGISTER,
                    block_number=block_number,
                )
                return
            dataset.onchain_id = onchain_id
            dataset.status = DatasetStatus.READY
            dataset.progress = 100
            await _record_tx(
                db,
                tx_hash=tx_hash,
                action=BlockchainActionType.DATASET_REGISTER,
                block_number=block_number,
                user_id=dataset.owner_id,
            )

        await get_ws_manager().publish(
            RealtimeEvent(
                type=EventType.STORAGE_ANCHORED,
                topic=f"dataset:{onchain_id}",
                payload={
                    "onchain_id": onchain_id,
                    "tx_hash": tx_hash,
                    "indexer": True,
                },
            )
        )

    async def _on_dataset_minted(self, entry: dict[str, Any]) -> None:
        topics_ = [t.hex() if hasattr(t, "hex") else t for t in entry["topics"]]
        token_id = int(topics_[1], 16)
        dataset_onchain_id = int(topics_[2], 16)
        owner = "0x" + topics_[3][-40:]
        tx_hash = entry["transactionHash"].hex() if hasattr(entry["transactionHash"], "hex") else entry["transactionHash"]
        contract_addr = entry["address"]

        async with session_scope() as db:
            res = await db.execute(
                select(Dataset).where(Dataset.onchain_id == dataset_onchain_id)
            )
            dataset = res.scalar_one_or_none()
            if dataset is None:
                await _record_tx(
                    db,
                    tx_hash=tx_hash,
                    action=BlockchainActionType.DATASET_MINT,
                    contract_address=contract_addr,
                )
                return

            res_nft = await db.execute(
                select(DatasetNFT).where(DatasetNFT.dataset_id == dataset.id)
            )
            nft = res_nft.scalar_one_or_none()
            if nft is None:
                nft = DatasetNFT(
                    dataset_id=dataset.id,
                    token_id=token_id,
                    contract_address=contract_addr,
                    owner_wallet=owner,
                    mint_tx_hash=tx_hash,
                )
                db.add(nft)
            else:
                nft.token_id = token_id
                nft.contract_address = contract_addr
                nft.owner_wallet = owner
                if not nft.mint_tx_hash:
                    nft.mint_tx_hash = tx_hash

            await _record_tx(
                db,
                tx_hash=tx_hash,
                action=BlockchainActionType.DATASET_MINT,
                contract_address=contract_addr,
                user_id=dataset.owner_id,
            )

    async def _on_training_started(self, entry: dict[str, Any]) -> None:
        topics_ = [t.hex() if hasattr(t, "hex") else t for t in entry["topics"]]
        job_id = int(topics_[1], 16)
        dataset_onchain_id = int(topics_[2], 16)
        operator = "0x" + topics_[3][-40:]
        tx_hash = entry["transactionHash"].hex() if hasattr(entry["transactionHash"], "hex") else entry["transactionHash"]

        async with session_scope() as db:
            res = await db.execute(
                select(TrainingJob)
                .where(TrainingJob.contract_job_id == job_id)
            )
            job = res.scalar_one_or_none()
            if job is None:
                # Best-effort: link to most recent matching dataset by onchain_id.
                res_ds = await db.execute(
                    select(Dataset).where(Dataset.onchain_id == dataset_onchain_id)
                )
                ds = res_ds.scalar_one_or_none()
                if ds is not None:
                    res_job = await db.execute(
                        select(TrainingJob)
                        .where(TrainingJob.dataset_id == ds.id)
                        .where(TrainingJob.contract_job_id.is_(None))
                        .order_by(TrainingJob.created_at.desc())
                        .limit(1)
                    )
                    job = res_job.scalar_one_or_none()
                    if job is not None:
                        job.contract_job_id = job_id
                        job.chain_start_tx_hash = tx_hash

            await _record_tx(
                db,
                tx_hash=tx_hash,
                action=BlockchainActionType.TRAINING_START,
                user_id=job.user_id if job else None,
                extra={"operator": operator, "dataset_onchain_id": dataset_onchain_id},
            )

        await get_ws_manager().publish(
            RealtimeEvent(
                type=EventType.TRAIN_STARTED,
                topic=f"training:contract:{job_id}",
                payload={"tx_hash": tx_hash, "indexer": True},
            )
        )

    async def _on_training_updated(self, entry: dict[str, Any]) -> None:
        topics_ = [t.hex() if hasattr(t, "hex") else t for t in entry["topics"]]
        job_id = int(topics_[1], 16)
        tx_hash = entry["transactionHash"].hex() if hasattr(entry["transactionHash"], "hex") else entry["transactionHash"]
        async with session_scope() as db:
            await _record_tx(
                db,
                tx_hash=tx_hash,
                action=BlockchainActionType.TRAINING_UPDATE,
                extra={"contract_job_id": job_id},
            )

    async def _on_training_completed(self, entry: dict[str, Any]) -> None:
        topics_ = [t.hex() if hasattr(t, "hex") else t for t in entry["topics"]]
        job_id = int(topics_[1], 16)
        tx_hash = entry["transactionHash"].hex() if hasattr(entry["transactionHash"], "hex") else entry["transactionHash"]

        async with session_scope() as db:
            res = await db.execute(
                select(TrainingJob).where(TrainingJob.contract_job_id == job_id)
            )
            job = res.scalar_one_or_none()
            if job is not None:
                job.chain_complete_tx_hash = tx_hash
                if job.status not in (
                    TrainingJobStatus.SUCCEEDED,
                    TrainingJobStatus.FAILED,
                ):
                    job.status = TrainingJobStatus.SUCCEEDED
            await _record_tx(
                db,
                tx_hash=tx_hash,
                action=BlockchainActionType.TRAINING_COMPLETE,
                user_id=job.user_id if job else None,
                extra={"contract_job_id": job_id},
            )

        await get_ws_manager().publish(
            RealtimeEvent(
                type=EventType.TRAIN_COMPLETED,
                topic=f"training:contract:{job_id}",
                payload={"tx_hash": tx_hash, "indexer": True},
            )
        )


def _build_topic_index(w3) -> dict[str, str]:
    """Resolve event topic hashes for every event we care about."""
    out: dict[str, str] = {}
    for contract_name, names in (
        ("DatasetRegistry", ["DatasetRegistered"]),
        ("DatasetNFT", ["DatasetMinted"]),
        (
            "TrainingRegistry",
            ["TrainingStarted", "TrainingUpdated", "TrainingCompleted"],
        ),
    ):
        abi = load_abi(contract_name)
        if abi is None:
            return {}
        for name in names:
            sig = _event_topic(w3, abi, name)
            if sig is None:
                return {}
            out[name] = sig
    return out


async def _record_tx(
    db,
    *,
    tx_hash: str,
    action: BlockchainActionType,
    block_number: int | None = None,
    contract_address: str | None = None,
    user_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    res = await db.execute(
        select(BlockchainTransaction).where(BlockchainTransaction.tx_hash == tx_hash)
    )
    row = res.scalar_one_or_none()
    settings = get_settings()
    if row is None:
        row = BlockchainTransaction(
            user_id=user_id,
            tx_hash=tx_hash,
            chain_id=settings.og_chain_id,
            action_type=action,
            status=BlockchainTxStatus.CONFIRMED,
            contract_address=contract_address,
            block_number=block_number,
            extra=extra or {},
        )
        db.add(row)
        return
    row.status = BlockchainTxStatus.CONFIRMED
    if block_number is not None:
        row.block_number = block_number
    if contract_address and not row.contract_address:
        row.contract_address = contract_address
    if user_id and not row.user_id:
        row.user_id = user_id
    if extra:
        merged = dict(row.extra or {})
        merged.update(extra)
        row.extra = merged


_singleton: ChainIndexer | None = None


def get_indexer() -> ChainIndexer:
    global _singleton
    if _singleton is None:
        _singleton = ChainIndexer()
    return _singleton


async def start_indexer() -> None:
    await get_indexer().start()


async def stop_indexer() -> None:
    await get_indexer().shutdown()
