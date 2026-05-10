"""Centralised application configuration.

All settings are loaded from environment variables (or `.env` at the repo root).
Settings are immutable per process — `get_settings()` returns a cached instance.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Top-level configuration.

    The class is intentionally flat: `get_settings()` is called frequently and
    nested models slow down import + validation paths.
    """

    model_config = SettingsConfigDict(
        env_file=(str(REPO_ROOT / ".env"), str(REPO_ROOT / ".env.example")),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- General -----------------------------------------------------------
    env: Literal["development", "staging", "production"] = Field(
        default="development", alias="DATAMIND_ENV"
    )
    log_level: str = Field(default="INFO", alias="DATAMIND_LOG_LEVEL")

    # --- HTTP --------------------------------------------------------------
    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    backend_public_url: str = Field(
        default="http://localhost:8000", alias="BACKEND_PUBLIC_URL"
    )
    cors_origins_raw: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="BACKEND_CORS_ORIGINS",
    )

    # --- Auth --------------------------------------------------------------
    jwt_secret: SecretStr = Field(
        default=SecretStr("devsecret-change-me-32chars-min-xxxxxxxxxx"),
        alias="BACKEND_JWT_SECRET",
    )
    jwt_alg: str = Field(default="HS256", alias="BACKEND_JWT_ALG")
    jwt_ttl_seconds: int = Field(default=86_400, alias="BACKEND_JWT_TTL_SECONDS")

    # --- Rate limit & uploads ---------------------------------------------
    rate_limit_per_minute: int = Field(default=120, alias="BACKEND_RATE_LIMIT_PER_MINUTE")
    upload_dir: Path = Field(
        default=REPO_ROOT / "storage_local", alias="BACKEND_UPLOAD_DIR"
    )
    max_upload_mb: int = Field(default=200, alias="BACKEND_MAX_UPLOAD_MB")

    # --- Postgres ---------------------------------------------------------
    database_url: str = Field(
        default="postgresql+asyncpg://datamind:datamind@localhost:5432/datamind",
        alias="DATABASE_URL",
    )

    # --- Qdrant -----------------------------------------------------------
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: SecretStr | None = Field(default=None, alias="QDRANT_API_KEY")
    qdrant_collection: str = Field(default="datamind_chunks", alias="QDRANT_COLLECTION")
    qdrant_vector_size: int = Field(default=384, alias="QDRANT_VECTOR_SIZE")

    # --- Redis ------------------------------------------------------------
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # --- AI engine --------------------------------------------------------
    ai_engine_url: str = Field(default="http://localhost:8100", alias="AI_ENGINE_URL")
    ai_embedding_model: str = Field(
        default="BAAI/bge-small-en-v1.5", alias="AI_EMBEDDING_MODEL"
    )

    # --- 0G ---------------------------------------------------------------
    og_mock: bool = Field(default=True, alias="DATAMIND_OG_MOCK")
    og_evm_rpc: str = Field(
        default="https://evmrpc-testnet.0g.ai", alias="OG_EVM_RPC"
    )
    og_indexer_rpc: str = Field(
        default="https://indexer-storage-testnet-turbo.0g.ai",
        alias="OG_INDEXER_RPC",
    )
    og_private_key: SecretStr | None = Field(default=None, alias="OG_PRIVATE_KEY")
    og_chain_network: str = Field(
        default="galileo-testnet-16602", alias="OG_CHAIN_NETWORK"
    )
    og_chain_id: int = Field(default=16602, alias="OG_CHAIN_ID")
    dataset_registry_address: str | None = Field(
        default=None, alias="DATASET_REGISTRY_ADDRESS"
    )
    license_registry_address: str | None = Field(
        default=None, alias="LICENSE_REGISTRY_ADDRESS"
    )

    # --- Privy ------------------------------------------------------------
    privy_app_id: str | None = Field(default=None, alias="PRIVY_APP_ID")
    privy_app_secret: SecretStr | None = Field(default=None, alias="PRIVY_APP_SECRET")

    # --- Validators -------------------------------------------------------

    @field_validator("upload_dir", mode="after")
    @classmethod
    def _ensure_upload_dir(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v

    # --- Derived ----------------------------------------------------------

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]

    @property
    def chain_live(self) -> bool:
        """True when we should hit the real chain instead of mocking."""
        return (
            not self.og_mock
            and self.og_private_key is not None
            and self.og_private_key.get_secret_value().strip() != ""
            and self.dataset_registry_address is not None
        )

    @property
    def storage_live(self) -> bool:
        """True when 0G Storage uploads should hit the real testnet."""
        return (
            not self.og_mock
            and self.og_private_key is not None
            and self.og_private_key.get_secret_value().strip() != ""
        )

    @property
    def privy_live(self) -> bool:
        return self.privy_app_id is not None and self.privy_app_id.strip() != ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
