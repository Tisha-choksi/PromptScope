import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.job import JobStatus, MonitoringJob
from app.models.prompt import Prompt
from app.schemas.job import JobResponse
from app.schemas.prompt import PromptCreate, PromptResponse, PromptUpdate
from app.api.deps import get_orchestrator
from app.services.llm.orchestrator import LLMOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[PromptResponse])
async def list_prompts(
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[PromptResponse]:
    """Return all prompts, optionally filtered by active status."""
    stmt = select(Prompt).order_by(Prompt.id)
    if is_active is not None:
        stmt = stmt.where(Prompt.is_active == is_active)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    payload: PromptCreate,
    db: AsyncSession = Depends(get_db),
) -> PromptResponse:
    """Create a new monitoring prompt."""
    prompt = Prompt(**payload.model_dump())
    db.add(prompt)
    await db.flush()
    await db.refresh(prompt)
    return prompt


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: int,
    db: AsyncSession = Depends(get_db),
) -> PromptResponse:
    """Retrieve a single prompt by ID."""
    return await _get_prompt_or_404(prompt_id, db)


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: int,
    payload: PromptUpdate,
    db: AsyncSession = Depends(get_db),
) -> PromptResponse:
    """Update a prompt's fields."""
    prompt = await _get_prompt_or_404(prompt_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(prompt, field, value)
    await db.flush()
    await db.refresh(prompt)
    return prompt


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete a prompt by setting is_active=False."""
    prompt = await _get_prompt_or_404(prompt_id, db)
    prompt.is_active = False
    await db.flush()


@router.post("/{prompt_id}/run", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_prompt(
    prompt_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    orchestrator: LLMOrchestrator = Depends(get_orchestrator),
) -> JobResponse:
    """Manually trigger a monitoring job for this prompt.

    Creates a MonitoringJob record with status=PENDING, dispatches the
    pipeline as a background task, and returns the job immediately.
    """
    prompt = await _get_prompt_or_404(prompt_id, db)
    if not prompt.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot run an inactive prompt.",
        )

    available_providers = orchestrator.get_available_providers()
    if not available_providers:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No LLM providers are currently available.",
        )

    job = MonitoringJob(
        prompt_id=prompt_id,
        status=JobStatus.PENDING,
        providers=available_providers,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    # Dispatch the pipeline as a background task so the HTTP response is
    # returned immediately while execution happens asynchronously.
    job_id = job.id
    background_tasks.add_task(_dispatch_job, job_id)

    return job


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _dispatch_job(job_id: int) -> None:
    """Fire-and-forget wrapper called by BackgroundTasks."""
    from app.workers.job_processor import execute_monitoring_job

    try:
        await execute_monitoring_job(job_id)
    except Exception as exc:
        logger.exception("Background job %d raised an unhandled exception: %s", job_id, exc)


async def _get_prompt_or_404(prompt_id: int, db: AsyncSession) -> Prompt:
    result = await db.execute(select(Prompt).where(Prompt.id == prompt_id))
    prompt = result.scalar_one_or_none()
    if prompt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt {prompt_id} not found.",
        )
    return prompt
