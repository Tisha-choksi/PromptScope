from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DashboardStats(BaseModel):
    """High-level platform statistics shown on the main dashboard."""

    total_brands: int = 0
    total_prompts: int = 0
    total_jobs: int = 0
    avg_visibility_score: float = 0.0
    active_brands: int = 0
    active_prompts: int = 0
    jobs_last_24h: int = 0
    failed_jobs_last_24h: int = 0


class TrendPoint(BaseModel):
    """A single data point in a time-series visibility trend."""

    date: date
    visibility_score: float
    mention_count: int


class BrandTrend(BaseModel):
    """Time-series visibility trend for a single brand."""

    model_config = ConfigDict(from_attributes=True)

    brand_id: int
    brand_name: str
    trend_points: list[TrendPoint] = Field(default_factory=list)


class ProviderComparison(BaseModel):
    """Aggregated visibility metrics broken down by LLM provider."""

    provider: str
    mention_count: int = 0
    avg_rank: Optional[float] = None
    visibility_score: float = 0.0
    total_responses: int = 0
    mention_rate: float = Field(
        default=0.0,
        description="Fraction of responses that mention the brand (0–1)",
    )


class TopBrand(BaseModel):
    """Summary entry for a brand ranked by visibility, used in leaderboard views."""

    brand_id: int
    brand_name: str
    visibility_score: float
    mention_count: int
    rank_change: int = Field(
        default=0,
        description="Change in rank compared to the previous period; positive means improved",
    )
    is_competitor: bool = False
    avg_rank: Optional[float] = None
