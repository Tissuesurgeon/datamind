"""Web3 upgrade: dataset_nfts, blockchain_transactions, training chain linkage,
plus a `pending_chain` value on the `dataset_status` enum.

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()

    # ---- Extend dataset_status enum ----------------------------------------
    # ALTER TYPE ... ADD VALUE is non-transactional in some Postgres versions;
    # use `COMMIT` shim via execute IF NOT EXISTS for idempotency.
    op.execute(
        "ALTER TYPE dataset_status ADD VALUE IF NOT EXISTS 'pending_chain'"
    )

    # ---- New enums for blockchain_transactions -----------------------------
    action_type = postgresql.ENUM(
        "dataset_register",
        "dataset_mint",
        "dataset_update",
        "training_start",
        "training_update",
        "training_complete",
        "usage_pay",
        "other",
        name="blockchain_action_type",
    )
    tx_status = postgresql.ENUM(
        "pending",
        "confirmed",
        "failed",
        name="blockchain_tx_status",
    )
    action_type.create(bind, checkfirst=True)
    tx_status.create(bind, checkfirst=True)

    action_type_col = postgresql.ENUM(
        "dataset_register",
        "dataset_mint",
        "dataset_update",
        "training_start",
        "training_update",
        "training_complete",
        "usage_pay",
        "other",
        name="blockchain_action_type",
        create_type=False,
    )
    tx_status_col = postgresql.ENUM(
        "pending",
        "confirmed",
        "failed",
        name="blockchain_tx_status",
        create_type=False,
    )

    # ---- dataset_nfts ------------------------------------------------------
    op.create_table(
        "dataset_nfts",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column(
            "dataset_id",
            sa.String(length=26),
            sa.ForeignKey("datasets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_id", sa.BigInteger(), nullable=False),
        sa.Column("contract_address", sa.String(length=64), nullable=False),
        sa.Column("owner_wallet", sa.String(length=64), nullable=False),
        sa.Column("mint_tx_hash", sa.String(length=80), nullable=True),
        sa.Column("register_tx_hash", sa.String(length=80), nullable=True),
        sa.Column("token_uri", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("dataset_id", name="uq_dataset_nfts_dataset"),
        sa.UniqueConstraint(
            "contract_address", "token_id", name="uq_dataset_nfts_contract_token"
        ),
    )
    op.create_index("ix_dataset_nfts_dataset_id", "dataset_nfts", ["dataset_id"])
    op.create_index("ix_dataset_nfts_contract", "dataset_nfts", ["contract_address"])
    op.create_index("ix_dataset_nfts_owner", "dataset_nfts", ["owner_wallet"])

    # ---- blockchain_transactions ------------------------------------------
    op.create_table(
        "blockchain_transactions",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(length=26),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("tx_hash", sa.String(length=80), nullable=False),
        sa.Column("chain_id", sa.Integer(), nullable=True),
        sa.Column("action_type", action_type_col, nullable=False),
        sa.Column(
            "status",
            tx_status_col,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("contract_address", sa.String(length=64), nullable=True),
        sa.Column("block_number", sa.Integer(), nullable=True),
        sa.Column(
            "extra",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_blockchain_tx_user", "blockchain_transactions", ["user_id"])
    op.create_index("ix_blockchain_tx_hash", "blockchain_transactions", ["tx_hash"])
    op.create_index(
        "ix_blockchain_tx_action", "blockchain_transactions", ["action_type"]
    )

    # ---- training_jobs chain columns --------------------------------------
    op.add_column(
        "training_jobs",
        sa.Column("contract_job_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "training_jobs",
        sa.Column("chain_start_tx_hash", sa.String(length=80), nullable=True),
    )
    op.add_column(
        "training_jobs",
        sa.Column("chain_complete_tx_hash", sa.String(length=80), nullable=True),
    )
    op.create_index(
        "ix_training_jobs_contract_job_id",
        "training_jobs",
        ["contract_job_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_training_jobs_contract_job_id", table_name="training_jobs")
    op.drop_column("training_jobs", "chain_complete_tx_hash")
    op.drop_column("training_jobs", "chain_start_tx_hash")
    op.drop_column("training_jobs", "contract_job_id")

    op.drop_index("ix_blockchain_tx_action", table_name="blockchain_transactions")
    op.drop_index("ix_blockchain_tx_hash", table_name="blockchain_transactions")
    op.drop_index("ix_blockchain_tx_user", table_name="blockchain_transactions")
    op.drop_table("blockchain_transactions")

    op.drop_index("ix_dataset_nfts_owner", table_name="dataset_nfts")
    op.drop_index("ix_dataset_nfts_contract", table_name="dataset_nfts")
    op.drop_index("ix_dataset_nfts_dataset_id", table_name="dataset_nfts")
    op.drop_table("dataset_nfts")

    op.execute("DROP TYPE IF EXISTS blockchain_tx_status")
    op.execute("DROP TYPE IF EXISTS blockchain_action_type")
    # Note: there's no way to drop a single enum label in Postgres; leaving
    # `pending_chain` on the dataset_status enum is harmless after downgrade.
