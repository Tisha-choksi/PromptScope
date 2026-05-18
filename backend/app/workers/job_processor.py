"""
job_processor.py
================
End-to-end monitoring-job execution pipeline.

Pipeline steps
--------------
1.  Load the MonitoringJob and its associated Prompt from the DB.
2.  Transition job status → RUNNING.
3.  Load all active Brand records from the DB.
4.  Query every available LLM provider concurrently via LLMOrchestrator.
5.  Persist raw LLMResponse rows to the DB.
6.  Extract brand mentions from each response text using EntityExtractor.
7.  Analyse sentiment for each mention using MentionAnalyzer.
8.  Persist BrandMention rows to the DB.
9.  Compute per-brand visibility scores using VisibilityScorer.
10. Persist AnalysisResult rows to the DB.
11. Transition job status → COMPLETED.
    On any unhandled exception → FAILED with error_message set.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.analysis import AnalysisResult, BrandMention
from app.models.brand import Brand
from app.models.job import JobStatus, MonitoringJob
from app.models.prompt import Prompt
from app.models.response import LLMResponse as LLMResponseModel
from app.services.extraction.entity_extractor import EntityExtractor
from app.services.extraction.mention_analyzer import MentionAnalyzer
from app.services.llm.orchestrator import LLMOrchestrator
from app.services.ranking.scorer import VisibilityScorer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


async def execute_monitoring_job(job_id: int) -> None:
    """Execute the full monitoring pipeline for *job_id*.

    This function opens its own database session so it can be called from
    both BackgroundTasks (FastAPI) and from the APScheduler worker without
    depending on the request-scoped session injected by ``get_db``.
    """
    async with AsyncSessionLocal() as session:
        try:
            await _run_pipeline(job_id, session)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Job %d pipeline raised an unhandled exception.", job_id)
            await _mark_failed(job_id, str(exc), session)
            raise


async def run_job_in_background(job_id: int) -> None:
    """Thin wrapper used when dispatching a job outside an async context."""
    try:
        await execute_monitoring_job(job_id)
    except Exception as exc:  # noqa: BLE001
        logger.error("Job %d failed: %s", job_id, exc)


# ---------------------------------------------------------------------------
# Internal pipeline
# ---------------------------------------------------------------------------


async def _run_pipeline(job_id: int, session: AsyncSession) -> None:
    # ------------------------------------------------------------------
    # Step 1 – Load the job and its prompt
    # ------------------------------------------------------------------
    job_result = await session.execute(
        select(MonitoringJob).where(MonitoringJob.id == job_id)
    )
    job: MonitoringJob | None = job_result.scalar_one_or_none()
    if job is None:
        raise ValueError(f"MonitoringJob {job_id} not found in the database.")

    prompt_result = await session.execute(
        select(Prompt).where(Prompt.id == job.prompt_id)
    )
    prompt: Prompt | None = prompt_result.scalar_one_or_none()
    if prompt is None:
        raise ValueError(
            f"Prompt {job.prompt_id} associated with job {job_id} not found."
        )

    # ------------------------------------------------------------------
    # Step 2 – Transition → RUNNING
    # ------------------------------------------------------------------
    job.status = JobStatus.RUNNING
    job.started_at = datetime.now(tz=timezone.utc)
    await session.flush()
    logger.info("Job %d started (prompt_id=%d).", job_id, job.prompt_id)

    # ------------------------------------------------------------------
    # Step 3 – Load all active brands
    # ------------------------------------------------------------------
    brands_result = await session.execute(
        select(Brand).where(Brand.is_active == True)  # noqa: E712
    )
    brands: list[Brand] = list(brands_result.scalars().all())
    if not brands:
        logger.warning("Job %d: no active brands found; scoring will be empty.", job_id)

    brands_dicts = [
        {"id": b.id, "name": b.name, "aliases": b.aliases or []} for b in brands
    ]

    # ------------------------------------------------------------------
    # Step 4 – Query LLM providers concurrently
    # ------------------------------------------------------------------
    orchestrator = LLMOrchestrator()
    providers_to_query = job.providers or orchestrator.get_available_providers()
    if not providers_to_query:
        raise RuntimeError("No LLM providers are available to query.")

    llm_responses = await orchestrator.query_all(
        prompt=prompt.text,
        providers=providers_to_query,
    )
    logger.info(
        "Job %d: received %d LLM responses from providers %s.",
        job_id,
        len(llm_responses),
        providers_to_query,
    )

    # ------------------------------------------------------------------
    # Step 5 – Persist raw LLMResponse records
    # ------------------------------------------------------------------
    db_responses: list[LLMResponseModel] = []
    for llm_resp in llm_responses:
        db_resp = LLMResponseModel(
            job_id=job_id,
            provider=llm_resp.provider,
            model=llm_resp.model,
            prompt_text=llm_resp.prompt_text,
            response_text=llm_resp.response_text or "",
            tokens_used=llm_resp.tokens_used,
            latency_ms=llm_resp.latency_ms,
            error=llm_resp.error,
        )
        session.add(db_resp)
        db_responses.append(db_resp)

    await session.flush()  # Assigns IDs to db_responses

    # ------------------------------------------------------------------
    # Step 6 – Extract brand mentions from each response
    # ------------------------------------------------------------------
    extractor = EntityExtractor(brands_dicts)
    analyzer = MentionAnalyzer()

    # Keep a mapping from (provider_name → db_response) for provider attribution
    provider_to_db_resp: dict[str, LLMResponseModel] = {
        r.provider: r for r in db_responses
    }

    # All analyzed mentions (across providers) used later for scoring
    all_analyzed_mentions = []

    # ------------------------------------------------------------------
    # Step 7 – Analyse sentiment per mention
    # ------------------------------------------------------------------
    for llm_resp in llm_responses:
        if not llm_resp.success or not llm_resp.response_text:
            continue  # Skip failed / empty responses

        db_resp = provider_to_db_resp.get(llm_resp.provider)
        if db_resp is None:
            continue

        raw_mentions = extractor.extract_mentions(llm_resp.response_text)
        analyzed_mentions = analyzer.analyze_mentions(raw_mentions)
        all_analyzed_mentions.extend(analyzed_mentions)

        # ------------------------------------------------------------------
        # Step 8 – Persist BrandMention records
        # ------------------------------------------------------------------
        for mention in analyzed_mentions:
            db_mention = BrandMention(
                response_id=db_resp.id,
                brand_id=mention.brand_id,
                mention_text=mention.text,
                position=mention.position,
                rank=mention.rank,
                context=mention.context,
                sentiment=mention.sentiment.value,
                confidence=mention.confidence,
            )
            session.add(db_mention)

    await session.flush()
    logger.info(
        "Job %d: extracted and saved %d brand mentions.",
        job_id,
        len(all_analyzed_mentions),
    )

    # ------------------------------------------------------------------
    # Step 9 – Compute visibility scores
    # ------------------------------------------------------------------
    scorer = VisibilityScorer()
    brand_scores = scorer.compute_all_brands(
        mentions=all_analyzed_mentions,
        responses=llm_responses,
        brands=brands_dicts,
    )

    # ------------------------------------------------------------------
    # Step 10 – Persist AnalysisResult records
    # ------------------------------------------------------------------
    for score in brand_scores:
        analysis = AnalysisResult(
            job_id=job_id,
            brand_id=score.brand_id,
            mention_count=score.mention_count,
            avg_rank=score.avg_rank,
            first_rank=score.first_rank,
            positive_mentions=score.positive_mentions,
            neutral_mentions=score.neutral_mentions,
            negative_mentions=score.negative_mentions,
            visibility_score=score.visibility_score,
            providers_mentioned_in=score.providers_mentioned_in,
        )
        session.add(analysis)

    await session.flush()
    logger.info(
        "Job %d: saved %d analysis results.",
        job_id,
        len(brand_scores),
    )

    # ------------------------------------------------------------------
    # Step 11 – Transition → COMPLETED
    # ------------------------------------------------------------------
    job.status = JobStatus.COMPLETED
    job.completed_at = datetime.now(tz=timezone.utc)
    await session.commit()
    logger.info("Job %d completed successfully.", job_id)


# ---------------------------------------------------------------------------
# Error recovery helper
# ---------------------------------------------------------------------------


async def _mark_failed(job_id: int, error_message: str, session: AsyncSession) -> None:
    """Best-effort attempt to mark the job as FAILED.

    Uses a fresh session if the current one might be corrupted.
    """
    try:
        await session.rollback()
        job_result = await session.execute(
            select(MonitoringJob).where(MonitoringJob.id == job_id)
        )
        job = job_result.scalar_one_or_none()
        if job is not None:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(tz=timezone.utc)
            job.error_message = error_message[:2048]  # guard against huge tracebacks
            await session.commit()
            logger.info("Job %d marked as FAILED.", job_id)
    except Exception as inner_exc:  # noqa: BLE001
        logger.error(
            "Failed to mark job %d as FAILED (secondary error): %s",
            job_id,
            inner_exc,
        )
        # If the session is truly broken, open a brand-new one.
        try:
            async with AsyncSessionLocal() as fresh_session:
                job_result = await fresh_session.execute(
                    select(MonitoringJob).where(MonitoringJob.id == job_id)
                )
                job = job_result.scalar_one_or_none()
                if job is not None:
                    job.status = JobStatus.FAILED
                    job.completed_at = datetime.now(tz=timezone.utc)
                    job.error_message = error_message[:2048]
                    await fresh_session.commit()
        except Exception:  # noqa: BLE001
            logger.exception(
                "Completely unable to persist FAILED status for job %d.", job_id
            )
