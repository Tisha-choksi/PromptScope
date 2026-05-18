import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.job import JobStatus, MonitoringJob
from app.models.analysis import AnalysisResult
from app.schemas.job import JobResponse, JobWithResults
from app.schemas.analysis import AnalysisResultResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    status_filter: Optional[JobStatus] = Query(
        default=None, alias="status", description="Filter by job status"
    ),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[JobResponse]:
    """Return a paginated list of monitoring jobs, optionally filtered by status."""
    stmt = select(MonitoringJob).order_by(MonitoringJob.id.desc())
    if status_filter is not None:
        stmt = stmt.where(MonitoringJob.status == status_filter)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{job_id}", response_model=JobWithResults)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
) -> JobWithResults:
    """Retrieve a single job together with its LLM responses and analysis results."""
    stmt = (
        select(MonitoringJob)
        .where(MonitoringJob.id == job_id)
        .options(
            selectinload(MonitoringJob.responses),
            selectinload(MonitoringJob.analysis_results),
        )
    )
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found.",
        )
    return job


@router.get("/{job_id}/results", response_model=list[AnalysisResultResponse])
async def get_job_results(
    job_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[AnalysisResultResponse]:
    """Return the detailed analysis results for a specific job."""
    # Verify job exists
    job_check = await db.execute(
        select(MonitoringJob).where(MonitoringJob.id == job_id)
    )
    if job_check.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found.",
        )

    stmt = (
        select(AnalysisResult)
        .where(AnalysisResult.job_id == job_id)
        .order_by(AnalysisResult.visibility_score.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Cancel a pending job.  Only jobs in PENDING status can be cancelled."""
    result = await db.execute(select(MonitoringJob).where(MonitoringJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found.",
        )
    if job.status != JobStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PENDING jobs can be cancelled. Current status: {job.status}.",
        )
    job.status = JobStatus.CANCELLED
    await db.flush()
