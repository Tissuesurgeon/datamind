"""Web3 inspection endpoints — public chain config + recent on-chain receipts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import desc, select

from app.core.config import get_settings
from app.core.deps import DBSession
from app.models.blockchain_tx import (
    BlockchainActionType,
    BlockchainTransaction,
    BlockchainTxStatus,
)

router = APIRouter()


class ChainConfigOut(BaseModel):
    chain_id: int
    rpc_url: str
    explorer_url: str | None
    contracts: dict[str, str | None]
    web3_user_tx: bool
    indexer_enabled: bool
    og_mock: bool
    chain_live: bool


class TxOut(BaseModel):
    id: str
    user_id: str | None
    tx_hash: str
    chain_id: int | None
    action_type: BlockchainActionType
    status: BlockchainTxStatus
    contract_address: str | None
    block_number: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/config", response_model=ChainConfigOut)
async def chain_config() -> ChainConfigOut:
    s = get_settings()
    return ChainConfigOut(
        chain_id=s.og_chain_id,
        rpc_url=s.og_evm_rpc,
        explorer_url=None,  # surfaced via NEXT_PUBLIC_OG_EXPLORER_URL on the FE
        contracts={
            "DatasetRegistry": s.dataset_registry_address,
            "DatasetNFT": s.dataset_nft_address,
            "TrainingRegistry": s.training_registry_address,
            "UsageEconomy": s.usage_economy_address,
            "LicenseRegistry": s.license_registry_address,
        },
        web3_user_tx=s.web3_user_tx,
        indexer_enabled=s.chain_indexer_enabled,
        og_mock=s.og_mock,
        chain_live=s.chain_live,
    )


@router.get("/events", response_model=list[TxOut])
async def recent_events(
    db: DBSession,
    limit: int = Query(50, ge=1, le=200),
    action: Literal[
        "dataset_register",
        "dataset_mint",
        "dataset_update",
        "training_start",
        "training_update",
        "training_complete",
        "usage_pay",
        "other",
    ]
    | None = None,
) -> list[TxOut]:
    stmt = select(BlockchainTransaction).order_by(desc(BlockchainTransaction.created_at))
    if action is not None:
        stmt = stmt.where(
            BlockchainTransaction.action_type == BlockchainActionType(action)
        )
    rows = (await db.execute(stmt.limit(limit))).scalars().all()
    return [TxOut.model_validate(r) for r in rows]
