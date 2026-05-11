"""Persist a user-signed mint + register receipt onto a pending dataset.

Called by `POST /api/v1/datasets/{id}/chain-confirm` when the frontend has the
on-chain receipts from `wagmi.useWaitForTransactionReceipt`. Idempotent: posting
the same hashes twice keeps the dataset in a consistent READY state.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.blockchain_tx import (
    BlockchainActionType,
    BlockchainTransaction,
    BlockchainTxStatus,
)
from app.models.dataset import Dataset, DatasetStatus
from app.models.dataset_nft import DatasetNFT
from app.schemas.dataset import DatasetChainConfirm
from app.services.realtime import EventType, RealtimeEvent, get_ws_manager

log = get_logger(__name__)


async def confirm_chain(
    db: AsyncSession,
    *,
    dataset: Dataset,
    payload: DatasetChainConfirm,
) -> Dataset:
    settings = get_settings()

    # Update dataset core chain refs.
    dataset.onchain_id = payload.onchain_id
    if payload.chain_id is not None:
        dataset.chain_id = payload.chain_id
    elif dataset.chain_id is None:
        dataset.chain_id = settings.og_chain_id
    dataset.status = DatasetStatus.READY
    dataset.progress = 100

    # Upsert the dataset NFT mirror (only if we have any nft info).
    if payload.token_id is not None and payload.nft_contract:
        existing = await db.execute(
            select(DatasetNFT).where(DatasetNFT.dataset_id == dataset.id)
        )
        nft = existing.scalar_one_or_none()
        owner_wallet = dataset.owner.wallet_address if dataset.owner else ""
        if nft is None:
            nft = DatasetNFT(
                dataset_id=dataset.id,
                token_id=payload.token_id,
                contract_address=payload.nft_contract,
                owner_wallet=owner_wallet,
                mint_tx_hash=payload.mint_tx_hash,
                register_tx_hash=payload.register_tx_hash,
            )
            db.add(nft)
        else:
            nft.token_id = payload.token_id
            nft.contract_address = payload.nft_contract
            nft.mint_tx_hash = payload.mint_tx_hash or nft.mint_tx_hash
            nft.register_tx_hash = payload.register_tx_hash or nft.register_tx_hash
            if owner_wallet:
                nft.owner_wallet = owner_wallet

    # Record tx receipts for the audit ledger.
    user_id = dataset.owner_id
    for tx_hash, action in (
        (payload.mint_tx_hash, BlockchainActionType.DATASET_MINT),
        (payload.register_tx_hash, BlockchainActionType.DATASET_REGISTER),
    ):
        if not tx_hash:
            continue
        await _record_tx(
            db,
            user_id=user_id,
            tx_hash=tx_hash,
            action=action,
            chain_id=payload.chain_id or settings.og_chain_id,
            contract_address=payload.nft_contract,
        )

    await get_ws_manager().publish(
        RealtimeEvent(
            type=EventType.STORAGE_ANCHORED,
            topic=f"dataset:{dataset.id}",
            payload={
                "dataset_id": dataset.id,
                "onchain_id": payload.onchain_id,
                "token_id": payload.token_id,
                "mint_tx_hash": payload.mint_tx_hash,
                "register_tx_hash": payload.register_tx_hash,
                "chain_id": dataset.chain_id,
                "confirmed": True,
            },
        )
    )
    return dataset


async def _record_tx(
    db: AsyncSession,
    *,
    user_id: str | None,
    tx_hash: str,
    action: BlockchainActionType,
    chain_id: int | None,
    contract_address: str | None,
) -> None:
    existing = await db.execute(
        select(BlockchainTransaction).where(BlockchainTransaction.tx_hash == tx_hash)
    )
    row = existing.scalar_one_or_none()
    if row is None:
        row = BlockchainTransaction(
            user_id=user_id,
            tx_hash=tx_hash,
            chain_id=chain_id,
            action_type=action,
            status=BlockchainTxStatus.CONFIRMED,
            contract_address=contract_address,
            extra={},
        )
        db.add(row)
        return
    row.status = BlockchainTxStatus.CONFIRMED
    if chain_id is not None and not row.chain_id:
        row.chain_id = chain_id
    if contract_address and not row.contract_address:
        row.contract_address = contract_address
