"""Dataset-related schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

QualityGrade = Literal["A", "B", "C"]
DatasetCategory = Literal[
    "Finance",
    "NLP",
    "Web3",
    "Tabular",
    "Vision",
    "Audio",
    "Other",
]


class DatasetCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    category: DatasetCategory = "Other"
    tags: list[str] = Field(default_factory=list)
    visibility: Literal["public", "private", "unlisted"] = "public"
    price_amount: float | None = None
    price_token: str | None = "OG"
    license_kind: Literal["personal", "commercial", "academic", "exclusive"] | None = None


class DatasetUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: DatasetCategory | None = None
    tags: list[str] | None = None
    visibility: Literal["public", "private", "unlisted"] | None = None
    price_amount: float | None = None
    license_kind: Literal["personal", "commercial", "academic", "exclusive"] | None = None


class DatasetSummary(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    category: str
    tags: list[str]
    quality_score: float | None
    quality_grade: QualityGrade | None
    ai_readiness: float | None
    rows: int
    embeddings_count: int
    downloads: int
    visibility: str
    status: str
    progress: int
    storage_root: str | None
    onchain_id: int | None
    owner_wallet: str
    created_at: datetime


class DatasetListItem(DatasetSummary):
    pass


class DatasetMarketplaceItem(DatasetSummary):
    description: str | None
    price_amount: float | None
    price_token: str | None
    license_kind: str | None


class DatasetDetail(DatasetSummary):
    description: str | None
    format: str
    size_bytes: int
    columns: int
    storage_tx_hash: str | None
    metadata_uri: str | None
    license_kind: str | None
    price_amount: float | None
    price_token: str | None
    summary: str | None = None
    semantic_tags: list[str] = []
    topics: list[dict] = []
    quality_metrics: dict = {}
    sample_rows: list[dict] = []
    # Web3 augmentation — populated when the dataset has been minted/registered.
    nft_contract: str | None = None
    nft_token_id: int | None = None
    mint_tx_hash: str | None = None
    register_tx_hash: str | None = None
    owner_address: str | None = None
    # Populated while status is pending_chain so the UI can drive wagmi without
    # relying solely on WebSocket delivery (clients may connect after the event).
    pending_chain_args: dict[str, Any] | None = None


class DatasetUploadResponse(BaseModel):
    dataset: DatasetSummary
    ws_topic: str


class DatasetChainConfirm(BaseModel):
    """Frontend → backend callback after user-signed mint + register.

    The on-chain indexer also publishes these events asynchronously; this
    endpoint exists so the UI can mark the dataset READY instantly without
    waiting for the indexer's polling tick.
    """

    onchain_id: int
    register_tx_hash: str | None = None
    mint_tx_hash: str | None = None
    token_id: int | None = None
    nft_contract: str | None = None
    chain_id: int | None = None
