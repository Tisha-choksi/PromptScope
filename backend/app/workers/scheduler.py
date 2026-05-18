"""
scheduler.py
============
APScheduler-based background scheduler for PromptScope.

Responsibilities
----------------
- Poll the DB every minute to find Prompts whose ``schedule_cron`` is due.
- For each overdue prompt, create a ``MonitoringJob`` and dispatch it to the
  job processor pipeline.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Module-level scheduler instance — started / stopped from app lifespan.
scheduler = AsyncIOScheduler()


# ---------------------------------------------------------------------------
# Public lifecycle helpers
# ---------------------------------------------------------------------------


async def setup_scheduler() -> None:
    """Initialize and start the APScheduler.

    Registers the scheduled-prompt checker to run every minute.
    Safe to call multiple times; the job ``replace_existing=True`` guard
    prevents duplicates on hot-reload.
    """
    scheduler.add_job(
        check_and_dispatch_scheduled_prompts,
        trigger=IntervalTrigger(minutes=1),
        id="check_scheduled_prompts",
        replace_existing=True,
        coalesce=True,       # skip missed fires to avoid pile-ups
        max_instances=1,     # prevent overlapping runs
    )
    scheduler.start()
    logger.info("APScheduler started.")


async def shutdown_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped.")


# ---------------------------------------------------------------------------
# Scheduled task
# ---------------------------------------------------------------------------


async def check_and_dispatch_scheduled_prompts() -> None:
    """Query the DB for prompts that are due to run according to their cron schedule.

    Algorithm
    ---------
    For each active prompt with a ``schedule_cron`` expression:
    1.  Find the most-recent MonitoringJob created for it (if any).
    2.  Use ``croniter`` to determine the previous expected fire time relative
        to *now*.
    3.  If no job exists after that expected fire time the prompt is considered
        overdue — create a new PENDING job and dispatch it.
    """
    from croniter import croniter  # imported lazily; not required at module level
    from sqlalchemy import select

    from app.database import AsyncSessionLocal
    from app.models.job import JobStatus, MonitoringJob
    from app.models.prompt import Prompt
    from app.services.llm.orchestrator import LLMOrchestrator
    from app.workers.job_processor import execute_monitoring_job

    now = datetime.now(tz=timezone.utc)

    try:
        async with AsyncSessionLocal() as session:
            # Load all active, scheduled prompts
            result = await session.execute(
                select(Prompt)
                .where(Prompt.is_active == True)  # noqa: E712
                .where(Prompt.schedule_cron.is_not(None))
            )
            prompts: list[Prompt] = list(result.scalars().all())

            if not prompts:
                return

            orchestrator = LLMOrchestrator()
            available_providers = orchestrator.get_available_providers()

            dispatched = 0
            for prompt in prompts:
                try:
                    should_run = await _prompt_is_due(prompt, now, session)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Could not evaluate schedule for prompt %d: %s",
                        prompt.id,
                        exc,
                    )
                    continue

                if not should_run:
                    continue

                job = MonitoringJob(
                    prompt_id=prompt.id,
                    status=JobStatus.PENDING,
                    providers=available_providers,
                )
                session.add(job)
                await session.flush()
                job_id = job.id
                await session.commit()

                logger.info(
                    "Scheduler created job %d for prompt %d (cron=%r).",
                    job_id,
                    prompt.id,
                    prompt.schedule_cron,
                )

                # Dispatch asynchronously — do not await so the scheduler
                # loop keeps moving.
                import asyncio

                asyncio.ensure_future(
                    _safe_execute_job(job_id),
                )
                dispatched += 1

        if dispatched:
            logger.info("Scheduler dispatched %d job(s) this cycle.", dispatched)

    except Exception as exc:  # noqa: BLE001
        logger.exception("Scheduler cycle failed: %s", exc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _prompt_is_due(
    prompt: "Prompt",
    now: datetime,
    session: "AsyncSession",
) -> bool:
    """Return True if *prompt* has not been run since its last expected cron fire."""
    from croniter import croniter
    from sqlalchemy import select

    from app.models.job import MonitoringJob

    if not prompt.schedule_cron:
        return False

    # Determine when the cron was *last* expected to fire (i.e. the most
    # recent fire time in the past relative to *now*).
    try:
        cron = croniter(prompt.schedule_cron, now)
        last_expected: datetime = cron.get_prev(datetime)
        # croniter returns naive datetimes; make it UTC-aware.
        if last_expected.tzinfo is None:
            last_expected = last_expected.replace(tzinfo=timezone.utc)
    except Exception as exc:
        raise ValueError(f"Invalid cron expression '{prompt.schedule_cron}': {exc}") from exc

    # Check whether a job for this prompt was created *after* the last
    # expected fire time.
    result = await session.execute(
        select(MonitoringJob)
        .where(MonitoringJob.prompt_id == prompt.id)
        .where(MonitoringJob.created_at >= last_expected)
        .limit(1)
    )
    existing_job = result.scalar_one_or_none()
    return existing_job is None  # no recent job → prompt is overdue


async def _safe_execute_job(job_id: int) -> None:
    """Wrapper that swallows exceptions so a failing job doesn't crash the event loop."""
    from app.workers.job_processor import execute_monitoring_job

    try:
        await execute_monitoring_job(job_id)
    except Exception as exc:  # noqa: BLE001
        logger.error("Scheduled job %d failed: %s", job_id, exc)
