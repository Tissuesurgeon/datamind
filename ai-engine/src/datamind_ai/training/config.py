"""Training configuration objects shared across the pipeline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TrainingConfig:
    job_id: str
    base_model: str = "Qwen/Qwen2.5-0.5B"
    task: str = "causal_lm"
    epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 2e-4
    lora_r: int = 8
    lora_alpha: int = 16
    max_seq_length: int = 512


SUPPORTED_BASE_MODELS = (
    "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "distilbert-base-uncased",
    "microsoft/phi-1_5",
    "Qwen/Qwen2.5-0.5B",
)
