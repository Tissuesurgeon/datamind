"""BlockchainTransaction — generic ledger of user-signed DataMind chain calls."""

from __future__ import annotations

import enum

from sqlalchemy import JSON, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class BlockchainActionType(str, enum.Enum):
    DATASET_REGISTER = "dataset_register"
    DATASET_MINT     = "dataset_mint"
    DATASET_UPDATE   = "dataset_update"
    TRAINING_START   = "training_start"
    TRAINING_UPDATE  = "training_update"
    TRAINING_COMPLETE = "training_complete"
    USAGE_PAY        = "usage_pay"
    OTHER            = "other"


class BlockchainTxStatus(str, enum.Enum):
    PENDING   = "pending"
    CONFIRMED = "confirmed"
    FAILED    = "failed"


class BlockchainTransaction(IdMixin, TimestampMixin, Base):
    __tablename__ = "blockchain_transactions"

    user_id: Mapped[str | None] = mapped_column(
        String(26), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    tx_hash: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    chain_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action_type: Mapped[BlockchainActionType] = mapped_column(
        SAEnum(
            BlockchainActionType,
            name="blockchain_action_type",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    status: Mapped[BlockchainTxStatus] = mapped_column(
        SAEnum(
            BlockchainTxStatus,
            name="blockchain_tx_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=BlockchainTxStatus.PENDING,
        nullable=False,
    )
    contract_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    block_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extra: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
