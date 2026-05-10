"""Training jobs API — create / list / fetch."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlalchemy import desc, select

from app.core.deps import CurrentUser, DBSession
from app.models.dataset import Dataset
from app.models.training_job import TrainingJob, TrainingJobStatus
from app.schemas.training import TrainingJobCreate, TrainingJobOut
from app.services.training.jobs import run_training_in_background

router = APIRouter()


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
