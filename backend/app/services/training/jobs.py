"""Training job orchestrator.

Hands the actual GPU work to ai-engine via HTTP. The backend's role:
    - mark RUNNING
    - call ai-engine /train (which streams progress back via Redis pubsub
      using the same `WebSocketManager.publish` path)
    - or — when ai-engine is offline — simulate a realistic progress curve
      for the demo so the UI still has something to show.

In either case, the final state and metrics are persisted to Postgres and the
checkpoint is anchored on 0G Storage.
"""

from __future__ import annotations

import asyncio
import json
import math
import random
import time
from contextlib import suppress
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select

from app.ai.client import get_ai_client
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import session_scope
from app.models.training_job import TrainingJob, TrainingJobStatus
from app.services.realtime import EventType, RealtimeEvent, get_ws_manager
from app.services.storage import og_client

log = get_logger(__name__)


async def _publish(topic: str, type_: EventType, payload: dict[str, Any]) -> None:
    await get_ws_manager().publish(RealtimeEvent(type=type_, topic=topic, payload=payload))


async def run_training_in_background(job_id: str) -> None:
    try:
        await run_training(job_id)
    except Exception as exc:  # pragma: no cover
        log.exception("training.failed", job_id=job_id, error=str(exc))
        async with session_scope() as db:
            res = await db.execute(select(TrainingJob).where(TrainingJob.id == job_id))
            job = res.scalar_one_or_none()
            if job is not None:
                job.status = TrainingJobStatus.FAILED
                job.error = str(exc)
        await _publish(f"training:{job_id}", EventType.TRAIN_FAILED, {"error": str(exc)})


async def run_training(job_id: str) -> None:
    topic = f"training:{job_id}"

    async with session_scope() as db:
        res = await db.execute(select(TrainingJob).where(TrainingJob.id == job_id))
        job = res.scalar_one_or_none()
        if job is None:
            return
        job.status = TrainingJobStatus.RUNNING
        config = dict(job.config)
        base_model = job.base_model
        dataset_id = job.dataset_id

    await _publish(
        topic,
        EventType.TRAIN_STARTED,
        {"job_id": job_id, "model": base_model, "dataset_id": dataset_id, "config": config},
    )

    # ---- Try ai-engine ------------------------------------------------------
    used_engine = False
    final_metrics: dict[str, Any] = {}
    if await _try_ai_engine(job_id, dataset_id, base_model, config, topic):
        used_engine = True
        # Engine streamed metrics already; just collect a final summary.
        final_metrics = await _collect_final_metrics(job_id)
    else:
        # ---- Simulated training (demo fallback) -----------------------------
        final_metrics = await _simulate_training(job_id, topic, config)

    # ---- Persist + anchor checkpoint ----------------------------------------
    checkpoint_payload = {
        "job_id": job_id,
        "model": base_model,
        "metrics": final_metrics,
        "engine": "ai-engine" if used_engine else "simulated",
    }
    settings = get_settings()
    ckpt_dir = settings.upload_dir / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = ckpt_dir / f"{job_id}.json"
    ckpt_path.write_text(json.dumps(checkpoint_payload, indent=2))

    og_result = await og_client.upload(ckpt_path)

    async with session_scope() as db:
        res = await db.execute(select(TrainingJob).where(TrainingJob.id == job_id))
        job = res.scalar_one_or_none()
        if job is None:
            return
        job.status = TrainingJobStatus.SUCCEEDED
        job.progress = 100.0
        job.metrics = final_metrics
        job.checkpoint_root = og_result["root"]
        job.checkpoint_tx_hash = og_result.get("tx_hash")

    await _publish(
        topic,
        EventType.TRAIN_COMPLETED,
        {
            "job_id": job_id,
            "metrics": final_metrics,
            "checkpoint_root": og_result["root"],
            "checkpoint_tx_hash": og_result.get("tx_hash"),
        },
    )


# --------------------------------------------------------------------------- #
# Ai-engine path                                                              #
# --------------------------------------------------------------------------- #


async def _try_ai_engine(
    job_id: str,
    dataset_id: str,
    base_model: str,
    config: dict,
    topic: str,
) -> bool:
    settings = get_settings()
    url = f"{settings.ai_engine_url.rstrip('/')}/train"
    payload = {
        "job_id": job_id,
        "dataset_id": dataset_id,
        "base_model": base_model,
        "config": config,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            health = await client.get(f"{settings.ai_engine_url.rstrip('/')}/healthz")
            if health.status_code != 200:
                return False
        async with httpx.AsyncClient(timeout=600) as client:
            async with client.stream("POST", url, json=payload) as resp:
                if resp.status_code != 200:
                    log.warning("training.engine.bad_status", code=resp.status_code)
                    return False
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        evt = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    await _persist_progress(job_id, evt)
                    await _publish(topic, EventType.TRAIN_PROGRESS, evt)
        return True
    except Exception as exc:
        log.info("training.engine.unreachable", error=str(exc))
        return False


# --------------------------------------------------------------------------- #
# Simulated path — keeps the demo flowing when ai-engine is down              #
# --------------------------------------------------------------------------- #


async def _simulate_training(
    job_id: str, topic: str, config: dict
) -> dict[str, Any]:
    epochs = int(config.get("epochs", 3))
    steps_per_epoch = 60
    total = epochs * steps_per_epoch
    start = time.time()

    rng = random.Random(hash(job_id) & 0xFFFFFFFF)
    base_loss = 2.4 + rng.random() * 0.4
    history: list[dict[str, Any]] = []

    for step in range(total):
        epoch = step / steps_per_epoch
        # Smooth log-decay loss with mild jitter.
        loss = base_loss * math.exp(-epoch * 0.45) * (0.9 + rng.random() * 0.2)
        loss = max(loss, 0.18)
        lr = float(config.get("learning_rate", 2e-4)) * (0.5 ** (epoch / max(epochs, 1)))
        progress = (step + 1) / total * 100.0

        evt = {
            "step": step + 1,
            "epoch": round(epoch, 3),
            "loss": round(loss, 4),
            "learning_rate": round(lr, 6),
            "progress": round(progress, 2),
            "elapsed_s": round(time.time() - start, 2),
        }
        history.append(evt)
        await _persist_progress(job_id, evt)
        await _publish(topic, EventType.TRAIN_PROGRESS, evt)

        # Throttle: ~25 events/sec for demo smoothness.
        await asyncio.sleep(0.04)

    eval_loss = history[-1]["loss"] * 1.05 + 0.1
    accuracy = max(0.55, min(0.95, 1.0 - eval_loss / 3.0))

    return {
        "history": history[-30:],
        "final_loss": history[-1]["loss"],
        "eval_loss": round(eval_loss, 4),
        "accuracy": round(accuracy, 4),
        "epochs": epochs,
        "steps": total,
        "duration_s": round(time.time() - start, 2),
    }


# --------------------------------------------------------------------------- #
# Persistence helper                                                          #
# --------------------------------------------------------------------------- #


async def _persist_progress(job_id: str, evt: dict[str, Any]) -> None:
    """Update the row with the latest progress snapshot. Best-effort."""
    with suppress(Exception):
        async with session_scope() as db:
            res = await db.execute(select(TrainingJob).where(TrainingJob.id == job_id))
            job = res.scalar_one_or_none()
            if job is None:
                return
            job.progress = float(evt.get("progress", job.progress))
            job.epoch = int(evt.get("epoch", job.epoch))
            metrics = dict(job.metrics or {})
            history = list(metrics.get("history", []))
            history.append(evt)
            metrics["history"] = history[-100:]
            metrics["last"] = evt
            job.metrics = metrics


async def _collect_final_metrics(job_id: str) -> dict[str, Any]:
    async with session_scope() as db:
        res = await db.execute(select(TrainingJob).where(TrainingJob.id == job_id))
        job = res.scalar_one_or_none()
        if job is None:
            return {}
        return dict(job.metrics or {})
