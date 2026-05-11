"""Training jobs API — create / list / fetch + chain-confirm callbacks."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlalchemy import desc, select

from app.core.config import get_settings
from app.core.deps import CurrentUser, DBSession
from app.models.blockchain_tx import (
    BlockchainActionType,
    BlockchainTransaction,
    BlockchainTxStatus,
)
from app.models.dataset import Dataset
from app.models.training_job import TrainingJob, TrainingJobStatus
from app.schemas.training import (
    TrainingChainCompleteConfirm,
    TrainingChainStartConfirm,
    TrainingJobCreate,
    TrainingJobOut,
)
from app.services.training.jobs import run_training_in_background

router = APIRouter()


async def _record_tx(
    db,
    *,
    user_id: str | None,
    tx_hash: str,
    action: BlockchainActionType,
    chain_id: int | None,
) -> None:
    res = await db.execute(
        select(BlockchainTransaction).where(BlockchainTransaction.tx_hash == tx_hash)
    )
    row = res.scalar_one_or_none()
    if row is None:
        db.add(
            BlockchainTransaction(
                user_id=user_id,
                tx_hash=tx_hash,
                chain_id=chain_id,
                action_type=action,
                status=BlockchainTxStatus.CONFIRMED,
                extra={},
            )
        )
        return
    row.status = BlockchainTxStatus.CONFIRMED
    if chain_id is not None and not row.chain_id:
        row.chain_id = chain_id


@router.post("/jobs", response_model=TrainingJobOut, status_code=status.HTTP_201_CREATED)
async def create_job(
    req: TrainingJobCreate,
    user: CurrentUser,
    db: DBSession,
    background: BackgroundTasks,
) -> TrainingJobOut:
    res = await db.execute(select(Dataset).where(Dataset.id == req.dataset_id))
    dataset = res.scalar_one_or_none()
    if dataset is None:
        raise HTTPException(status_code=404, detail="dataset not found")

    config = {
        "epochs": req.epochs,
        "batch_size": req.batch_size,
        "learning_rate": req.learning_rate,
        "lora_r": req.lora_r,
        "lora_alpha": req.lora_alpha,
        "max_seq_length": req.max_seq_length,
    }

    job = TrainingJob(
        user_id=user.id,
        dataset_id=req.dataset_id,
        name=req.name,
        base_model=req.base_model,
        task=req.task,
        config=config,
        status=TrainingJobStatus.PENDING,
        progress=0.0,
        epoch=0,
        metrics={},
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    background.add_task(run_training_in_background, job.id)
    return TrainingJobOut.model_validate(job)


@router.get("/jobs", response_model=list[TrainingJobOut])
async def list_jobs(user: CurrentUser, db: DBSession, limit: int = 50) -> list[TrainingJobOut]:
    res = await db.execute(
        select(TrainingJob)
        .where(TrainingJob.user_id == user.id)
        .order_by(desc(TrainingJob.created_at))
        .limit(limit)
    )
    return [TrainingJobOut.model_validate(j) for j in res.scalars().all()]


@router.get("/jobs/{job_id}", response_model=TrainingJobOut)
async def get_job(job_id: str, db: DBSession) -> TrainingJobOut:
    res = await db.execute(select(TrainingJob).where(TrainingJob.id == job_id))
    job = res.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return TrainingJobOut.model_validate(job)


@router.post("/jobs/{job_id}/chain-start", response_model=TrainingJobOut)
async def chain_start(
    job_id: str,
    payload: TrainingChainStartConfirm,
    user: CurrentUser,
    db: DBSession,
) -> TrainingJobOut:
    """Frontend → backend callback after `TrainingRegistry.createTrainingJob`
    confirms on-chain. Idempotent."""
    res = await db.execute(select(TrainingJob).where(TrainingJob.id == job_id))
    job = res.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    if job.user_id != user.id:
        raise HTTPException(status_code=403, detail="forbidden")

    job.contract_job_id = payload.contract_job_id
    job.chain_start_tx_hash = payload.tx_hash
    settings = get_settings()
    await _record_tx(
        db,
        user_id=user.id,
        tx_hash=payload.tx_hash,
        action=BlockchainActionType.TRAINING_START,
        chain_id=payload.chain_id or settings.og_chain_id,
    )
    await db.flush()
    await db.refresh(job)
    return TrainingJobOut.model_validate(job)


@router.post("/jobs/{job_id}/chain-complete", response_model=TrainingJobOut)
async def chain_complete(
    job_id: str,
    payload: TrainingChainCompleteConfirm,
    user: CurrentUser,
    db: DBSession,
) -> TrainingJobOut:
    res = await db.execute(select(TrainingJob).where(TrainingJob.id == job_id))
    job = res.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    if job.user_id != user.id:
        raise HTTPException(status_code=403, detail="forbidden")

    job.chain_complete_tx_hash = payload.tx_hash
    if payload.checkpoint_root and not job.checkpoint_root:
        job.checkpoint_root = payload.checkpoint_root
    settings = get_settings()
    await _record_tx(
        db,
        user_id=user.id,
        tx_hash=payload.tx_hash,
        action=BlockchainActionType.TRAINING_COMPLETE,
        chain_id=payload.chain_id or settings.og_chain_id,
    )
    await db.flush()
    await db.refresh(job)
    return TrainingJobOut.model_validate(job)
