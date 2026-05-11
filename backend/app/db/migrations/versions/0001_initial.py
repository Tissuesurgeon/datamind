"""Initial schema.

Revision ID: 0001
Revises:
Create Date: 2026-05-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Alembic's create_table fires enum DDL with checkfirst=False. In that path
    # PostgreSQL's EnumGenerator always emits CREATE TYPE if the column type
    # has create_type=True (the default). We therefore:
    # 1) CREATE TYPE ... up front with checkfirst=True
    # 2) use postgresql.ENUM(..., create_type=False) on columns so table DDL
    #    never tries to recreate the type (avoids DuplicateObject on retries).
    bind = op.get_bind()
    postgresql.ENUM(
        "public", "private", "unlisted", name="dataset_visibility"
    ).create(bind, checkfirst=True)
    postgresql.ENUM(
        "uploading", "processing", "ready", "failed", name="dataset_status"
    ).create(bind, checkfirst=True)
    postgresql.ENUM(
        "pending",
        "running",
        "succeeded",
        "failed",
        "cancelled",
        name="training_job_status",
    ).create(bind, checkfirst=True)
    postgresql.ENUM(
        "personal",
        "commercial",
        "academic",
        "exclusive",
        name="license_kind",
    ).create(bind, checkfirst=True)

    visibility = postgresql.ENUM(
        "public",
        "private",
        "unlisted",
        name="dataset_visibility",
        create_type=False,
    )
    status = postgresql.ENUM(
        "uploading",
        "processing",
        "ready",
        "failed",
        name="dataset_status",
        create_type=False,
    )
    train_status = postgresql.ENUM(
        "pending",
        "running",
        "succeeded",
        "failed",
        "cancelled",
        name="training_job_status",
        create_type=False,
    )
    license_kind = postgresql.ENUM(
        "personal",
        "commercial",
        "academic",
        "exclusive",
        name="license_kind",
        create_type=False,
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("wallet_address", sa.String(length=64), nullable=False, unique=True),
        sa.Column("email", sa.String(length=255), nullable=True, unique=True),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_wallet", "users", ["wallet_address"])

    op.create_table(
        "datasets",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("owner_id", sa.String(length=26), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("format", sa.String(length=16), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("columns", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("ai_readiness", sa.Float(), nullable=True),
        sa.Column("quality_grade", sa.String(length=2), nullable=True),
        sa.Column("embeddings_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("storage_root", sa.String(length=80), nullable=True),
        sa.Column("storage_tx_hash", sa.String(length=80), nullable=True),
        sa.Column("chain_id", sa.Integer(), nullable=True),
        sa.Column("onchain_id", sa.Integer(), nullable=True),
        sa.Column("metadata_uri", sa.String(length=512), nullable=True),
        sa.Column("visibility", visibility, nullable=False, server_default="public"),
        sa.Column("status", status, nullable=False, server_default="uploading"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("price_token", sa.String(length=16), nullable=True),
        sa.Column("price_amount", sa.Float(), nullable=True),
        sa.Column("license_kind", sa.String(length=32), nullable=True),
        sa.Column("downloads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_datasets_owner_id", "datasets", ["owner_id"])
    op.create_index("ix_datasets_category", "datasets", ["category"])
    op.create_index("ix_datasets_storage_root", "datasets", ["storage_root"])


    op.create_table(
        "dataset_files",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("dataset_id", sa.String(length=26), sa.ForeignKey("datasets.id", ondelete="CASCADE")),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("local_path", sa.String(length=1024), nullable=True),
        sa.Column("storage_root", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_dataset_files_dataset_id", "dataset_files", ["dataset_id"])
    op.create_index("ix_dataset_files_sha256", "dataset_files", ["sha256"])

    op.create_table(
        "dataset_embeddings",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("dataset_id", sa.String(length=26), sa.ForeignKey("datasets.id", ondelete="CASCADE")),
        sa.Column("vector_id", sa.String(length=64), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("chunk_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_dataset_embeddings_dataset_id", "dataset_embeddings", ["dataset_id"])
    op.create_index("ix_dataset_embeddings_vector_id", "dataset_embeddings", ["vector_id"])

    op.create_table(
        "dataset_analytics",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("dataset_id", sa.String(length=26), sa.ForeignKey("datasets.id", ondelete="CASCADE"), unique=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("semantic_tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("topics", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("quality_metrics", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("duplicate_ratio", sa.Float(), nullable=True),
        sa.Column("missing_ratio", sa.Float(), nullable=True),
        sa.Column("column_profile", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("sample_rows", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "training_jobs",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("user_id", sa.String(length=26), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("dataset_id", sa.String(length=26), sa.ForeignKey("datasets.id", ondelete="CASCADE")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("base_model", sa.String(length=128), nullable=False),
        sa.Column("task", sa.String(length=64), nullable=False, server_default="causal_lm"),
        sa.Column("config", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("status", train_status, nullable=False, server_default="pending"),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0"),
        sa.Column("epoch", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metrics", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("checkpoint_root", sa.String(length=80), nullable=True),
        sa.Column("checkpoint_tx_hash", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_training_user_id", "training_jobs", ["user_id"])
    op.create_index("ix_training_dataset_id", "training_jobs", ["dataset_id"])

    op.create_table(
        "dataset_licenses",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("dataset_id", sa.String(length=26), sa.ForeignKey("datasets.id", ondelete="CASCADE")),
        sa.Column("grantee_wallet", sa.String(length=64), nullable=False),
        sa.Column("kind", license_kind, nullable=False, server_default="personal"),
        sa.Column("onchain_id", sa.Integer(), nullable=True),
        sa.Column("tx_hash", sa.String(length=80), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_licenses_dataset_id", "dataset_licenses", ["dataset_id"])
    op.create_index("ix_licenses_grantee", "dataset_licenses", ["grantee_wallet"])
    op.create_index("ix_licenses_onchain", "dataset_licenses", ["onchain_id"])


def downgrade() -> None:
    op.drop_table("dataset_licenses")
    op.execute("DROP TYPE IF EXISTS license_kind")
    op.drop_table("training_jobs")
    op.execute("DROP TYPE IF EXISTS training_job_status")
    op.drop_table("dataset_analytics")
    op.drop_table("dataset_embeddings")
    op.drop_table("dataset_files")
    op.drop_table("datasets")
    op.execute("DROP TYPE IF EXISTS dataset_status")
    op.execute("DROP TYPE IF EXISTS dataset_visibility")
    op.drop_table("users")
