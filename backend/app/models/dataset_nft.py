"""DatasetNFT — local mirror of the on-chain ERC721 mint receipt."""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin


class DatasetNFT(IdMixin, TimestampMixin, Base):
    __tablename__ = "dataset_nfts"
    __table_args__ = (
        UniqueConstraint("dataset_id", name="uq_dataset_nfts_dataset"),
        UniqueConstraint(
            "contract_address",
            "token_id",
            name="uq_dataset_nfts_contract_token",
        ),
    )

    dataset_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("datasets.id", ondelete="CASCADE"), index=True
    )
    token_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    contract_address: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    owner_wallet: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    mint_tx_hash: Mapped[str | None] = mapped_column(String(80), nullable=True)
    register_tx_hash: Mapped[str | None] = mapped_column(String(80), nullable=True)
    token_uri: Mapped[str | None] = mapped_column(String(512), nullable=True)

    dataset: Mapped["Dataset"] = relationship(  # noqa: F821
        "Dataset", back_populates="nft"
    )
