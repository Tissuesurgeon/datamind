"""Default training entrypoint.

Always-streaming. By default uses a deterministic simulated curve so the
hackathon demo is fast + reproducible. Set `AI_LORA_REAL=1` to swap in the real
PEFT/TRL pipeline (`lora.lora_train`).
"""

from __future__ import annotations

import asyncio
import math
import random
import time
from collections.abc import AsyncIterator

from datamind_ai.training.config import TrainingConfig
from datamind_ai.training.lora import lora_train, real_train_supported


def _seed_from(job_id: str) -> int:
    return abs(hash(job_id)) & 0xFFFFFFFF


async def simulate_training_stream(cfg: TrainingConfig) -> AsyncIterator[dict]:
    """Yield realistic-looking training events at ~25 Hz."""
    rng = random.Random(_seed_from(cfg.job_id))
    epochs = cfg.epochs
    steps_per_epoch = 60
    total = epochs * steps_per_epoch
    base_loss = 2.4 + rng.random() * 0.4
    start = time.time()

    for step in range(total):
        epoch = step / steps_per_epoch
        loss = base_loss * math.exp(-epoch * 0.45) * (0.9 + rng.random() * 0.2)
        loss = max(loss, 0.18)
        lr = cfg.learning_rate * (0.5 ** (epoch / max(epochs, 1)))
        yield {
            "step": step + 1,
            "epoch": round(epoch, 3),
            "loss": round(loss, 4),
            "learning_rate": round(lr, 6),
            "progress": round((step + 1) / total * 100, 2),
            "elapsed_s": round(time.time() - start, 2),
        }
        await asyncio.sleep(0.04)


async def real_training_stream(cfg: TrainingConfig, dataset_text: str) -> AsyncIterator[dict]:
    # Generator wrapping; runs in a thread so we don't block the event loop.
    loop = asyncio.get_running_loop()

    def _produce() -> list[dict]:
        return list(lora_train(cfg, dataset_text))

    events = await loop.run_in_executor(None, _produce)
    for e in events:
        yield e


async def run_training(cfg: TrainingConfig, dataset_text: str = "") -> AsyncIterator[dict]:
    if real_train_supported() and dataset_text:
        async for evt in real_training_stream(cfg, dataset_text):
            yield evt
        return
    async for evt in simulate_training_stream(cfg):
        yield evt
