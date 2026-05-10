"""AI engine configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]  # ai-engine/src/datamind_ai → repo


class AIConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(REPO_ROOT / ".env"), str(REPO_ROOT / ".env.example")),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5", alias="AI_EMBEDDING_MODEL")
    hf_cache: Path = Field(default=REPO_ROOT / "hf-cache", alias="AI_HF_CACHE")
    lora_output_dir: Path = Field(
        default=REPO_ROOT / "checkpoints", alias="AI_LORA_OUTPUT_DIR"
    )
    port: int = Field(default=8100, alias="AI_ENGINE_PORT")
    backend_url: str = Field(default="http://localhost:8000", alias="BACKEND_PUBLIC_URL")

    # Default training base model when caller doesn't specify
    default_base_model: str = Field(
        default="Qwen/Qwen2.5-0.5B", alias="AI_DEFAULT_BASE_MODEL"
    )


@lru_cache(maxsize=1)
def get_config() -> AIConfig:
    cfg = AIConfig()  # type: ignore[call-arg]
    cfg.hf_cache.mkdir(parents=True, exist_ok=True)
    cfg.lora_output_dir.mkdir(parents=True, exist_ok=True)
    return cfg
