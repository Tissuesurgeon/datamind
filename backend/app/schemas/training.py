"""Training job schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SupportedBaseModel = Literal[
    "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "distilbert-base-uncased",
    "microsoft/phi-1_5",
    "Qwen/Qwen2.5-0.5B",
]


class TrainingJobCreate(BaseModel):
    model_config = {"protected_namespaces": ()}

    dataset_id: str
    name: str = Field(min_length=1, max_length=255)
    base_model: SupportedBaseModel = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    task: Literal["causal_lm", "classification"] = "causal_lm"
    epochs: int = Field(default=3, ge=1, le=20)
    batch_size: int = Field(default=4, ge=1, le=64)
    learning_rate: float = Field(default=2e-4, gt=0)
    lora_r: int = Field(default=8, ge=1, le=64)
    lora_alpha: int = Field(default=16, ge=1, le=128)
    max_seq_length: int = Field(default=512, ge=64, le=4096)


class TrainingMetricsPoint(BaseModel):
    step: int
    epoch: float
    loss: float
    learning_rate: float | None = None
    eval_loss: float | None = None
    accuracy: float | None = None


class TrainingJobOut(BaseModel):
    model_config = {"from_attributes": True, "protected_namespaces": ()}

    id: str
    name: str
    dataset_id: str
    base_model: str
    task: str
    status: str
    progress: float
    epoch: int
    metrics: dict
    error: str | None
    checkpoint_root: str | None
    checkpoint_tx_hash: str | None
    config: dict
    created_at: datetime
    updated_at: datetime
