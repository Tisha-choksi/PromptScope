import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_orchestrator
from app.models.analysis import AnalysisResult, BrandMention
from app.models.brand import Brand
from app.models.job import JobStatus, MonitoringJob
from app.models.prompt import Prompt
from app.models.response import LLMResponse
from app.schemas.analytics import (
    BrandTrend,
    DashboardStats,
    ProviderComparison,
    TopBrand,
    TrendPoint,
)
from app.services.llm.orchestrator import LLMOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    orchestrator: LLMOrchestrator = Depends(get_orchestrator),
) -> DashboardStats:
    """Return high-level platform statistics for the main dashboard."""
    now = datetime.now(tz=timezone.utc)

    # Counts
    total_brands = (await db.execute(select(func.count()).select_from(Brand))).scalar_one()
    active_brands = (
        await db.execute(select(func.count()).select_from(Brand).where(Brand.is_active == True))
    ).scalar_one()
    total_prompts = (await db.execute(select(func.count()).select_from(Prompt))).scalar_one()
    active_prompts = (
        await db.execute(select(func.count()).select_from(Prompt).where(Prompt.is_active == True))
    ).scalar_one()
    total_jobs = (await db.execute(select(func.count()).select_from(MonitoringJob))).scalar_one()
    jobs_last_24h = (
        await db.execute(
            select(func.count())
            .select_from(MonitoringJob)
            .where(MonitoringJob.created_at >= now - timedelta(hours=24))
        )
    ).scalar_one()
    failed_jobs_last_24h = (
        await db.execute(
            select(func.count())
            .select_from(MonitoringJob)
            .where(MonitoringJob.created_at >= now - timedelta(hours=24))
            .where(MonitoringJob.status == JobStatus.FAILED)
        )
    ).scalar_one()

    avg_vis = (
        await db.execute(select(func.avg(AnalysisResult.visibility_score)))
    ).scalar_one()

    return DashboardStats(
        total_brands=total_brands,
        total_prompts=total_prompts,
        total_jobs=total_jobs,
        avg_visibility_score=round(float(avg_vis or 0.0), 4),
        active_brands=active_brands,
        active_prompts=active_prompts,
        jobs_last_24h=jobs_last_24h,
        failed_jobs_last_24h=failed_jobs_last_24h,
    )


# ---------------------------------------------------------------------------
# Visibility trends
# ---------------------------------------------------------------------------


@router.get("/visibility-trends", response_model=list[BrandTrend])
async def get_visibility_trends(
    brand_ids: list[int] = Query(default=[], description="Brand IDs to include"),
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> list[BrandTrend]:
    """Return per-brand daily visibility trends over the requested time window."""
    since = datetime.now(tz=timezone.utc) - timedelta(days=days)

    # Resolve brand list — if caller didn't specify, use all active brands
    if brand_ids:
        brands_result = await db.execute(
            select(Brand).where(Brand.id.in_(brand_ids)).where(Brand.is_active == True)
        )
    else:
        brands_result = await db.execute(select(Brand).where(Brand.is_active == True))
    brands = brands_result.scalars().all()

    trends: list[BrandTrend] = []
    for brand in brands:
        # Pull analysis results within the window for this brand
        stmt = (
            select(AnalysisResult)
            .where(AnalysisResult.brand_id == brand.id)
            .where(AnalysisResult.created_at >= since)
            .order_by(AnalysisResult.created_at.asc())
        )
        results = (await db.execute(stmt)).scalars().all()

        # Aggregate by date
        daily: dict[date, list[AnalysisResult]] = {}
        for ar in results:
            # created_at is timezone-aware; normalise to a plain date
            d = ar.created_at.date() if hasattr(ar.created_at, "date") else ar.created_at
            daily.setdefault(d, []).append(ar)

        trend_points: list[TrendPoint] = []
        for day_date in sorted(daily.keys()):
            day_results = daily[day_date]
            avg_score = sum(r.visibility_score for r in day_results) / len(day_results)
            total_mentions = sum(r.mention_count for r in day_results)
            trend_points.append(
                TrendPoint(
                    date=day_date,
                    visibility_score=round(avg_score, 4),
                    mention_count=total_mentions,
                )
            )

        trends.append(
            BrandTrend(
                brand_id=brand.id,
                brand_name=brand.name,
                trend_points=trend_points,
            )
        )

    return trends


# ---------------------------------------------------------------------------
# Provider comparison
# ---------------------------------------------------------------------------


@router.get("/provider-comparison", response_model=dict)
async def get_provider_comparison(
    job_id: Optional[int] = Query(default=None, description="Restrict to a specific job"),
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Compare brand visibility scores across LLM providers.

    Returns a dict keyed by provider name, each containing a list of
    TopBrand entries ordered by visibility_score descending.
    """
    since = datetime.now(tz=timezone.utc) - timedelta(days=days)

    # Build base filter
    stmt = select(LLMResponse)
    if job_id is not None:
        stmt = stmt.where(LLMResponse.job_id == job_id)
    else:
        stmt = stmt.where(LLMResponse.created_at >= since)

    responses = (await db.execute(stmt)).scalars().all()

    # Collect unique providers in scope
    providers_in_scope: set[str] = {r.provider for r in responses}

    comparison: dict[str, list[dict]] = {}
    for provider in sorted(providers_in_scope):
        # Get analysis results for jobs that have this provider in their responses
        job_ids_for_provider = list(
            {r.job_id for r in responses if r.provider == provider}
        )
        if not job_ids_for_provider:
            comparison[provider] = []
            continue

        ar_stmt = (
            select(AnalysisResult, Brand.name.label("brand_name"))
            .join(Brand, AnalysisResult.brand_id == Brand.id)
            .where(AnalysisResult.job_id.in_(job_ids_for_provider))
            .where(AnalysisResult.providers_mentioned_in.contains([provider]))
            .order_by(AnalysisResult.visibility_score.desc())
        )
        ar_rows = (await db.execute(ar_stmt)).all()

        brand_map: dict[int, dict] = {}
        for ar, brand_name in ar_rows:
            if ar.brand_id not in brand_map:
                brand_map[ar.brand_id] = {
                    "brand_id": ar.brand_id,
                    "brand_name": brand_name,
                    "visibility_score": ar.visibility_score,
                    "mention_count": ar.mention_count,
                    "avg_rank": ar.avg_rank,
                }
            else:
                # Accumulate across multiple jobs
                existing = brand_map[ar.brand_id]
                existing["visibility_score"] = max(
                    existing["visibility_score"], ar.visibility_score
                )
                existing["mention_count"] += ar.mention_count

        comparison[provider] = sorted(
            brand_map.values(), key=lambda x: x["visibility_score"], reverse=True
        )

    return comparison


# ---------------------------------------------------------------------------
# Competitor comparison
# ---------------------------------------------------------------------------


@router.get("/competitor-comparison", response_model=list[TopBrand])
async def get_competitor_comparison(
    brand_ids: list[int] = Query(..., min_length=1, description="Brand IDs to compare"),
    db: AsyncSession = Depends(get_db),
) -> list[TopBrand]:
    """Side-by-side brand comparison ranked by average visibility score."""
    if not brand_ids:
        return []

    # Fetch brands
    brands_result = await db.execute(
        select(Brand).where(Brand.id.in_(brand_ids))
    )
    brands_by_id: dict[int, Brand] = {b.id: b for b in brands_result.scalars().all()}

    top_brands: list[TopBrand] = []
    for brand_id in brand_ids:
        brand = brands_by_id.get(brand_id)
        if brand is None:
            continue

        # Aggregate analysis results for this brand
        stmt = (
            select(
                func.avg(AnalysisResult.visibility_score).label("avg_score"),
                func.sum(AnalysisResult.mention_count).label("total_mentions"),
                func.avg(AnalysisResult.avg_rank).label("avg_rank"),
            )
            .where(AnalysisResult.brand_id == brand_id)
        )
        row = (await db.execute(stmt)).one()

        top_brands.append(
            TopBrand(
                brand_id=brand_id,
                brand_name=brand.name,
                visibility_score=round(float(row.avg_score or 0.0), 4),
                mention_count=int(row.total_mentions or 0),
                avg_rank=float(row.avg_rank) if row.avg_rank is not None else None,
                is_competitor=brand.is_competitor,
            )
        )

    # Rank by visibility score descending
    top_brands.sort(key=lambda b: b.visibility_score, reverse=True)
    return top_brands
