from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.analysis import SentimentLabel


class BrandMentionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    response_id: int
    brand_id: int
    mention_text: str
    position: int
    rank: Optional[int]
    context: Optional[str]
    sentiment: SentimentLabel
    confidence: float
    created_at: datetime


class AnalysisResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    brand_id: int
    mention_count: int
    avg_rank: Optional[float]
    first_rank: Optional[int]
    positive_mentions: int
    neutral_mentions: int
    negative_mentions: int
    visibility_score: float
    providers_mentioned_in: list[str]
    created_at: datetime


class VisibilityReport(BaseModel):
    """Aggregated visibility report for a brand across one or more jobs."""

    brand_id: int
    brand_name: str
    period_start: datetime
    period_end: datetime
    total_jobs: int
    total_mentions: int
    avg_visibility_score: float
    avg_rank: Optional[float]
    best_rank: Optional[int]
    sentiment_breakdown: dict[SentimentLabel, int] = Field(default_factory=dict)
    provider_breakdown: dict[str, int] = Field(default_factory=dict)
    mentions: list[BrandMentionResponse] = Field(default_factory=list)


class CompetitorComparison(BaseModel):
    """Side-by-side visibility comparison between a primary brand and competitors."""

    primary_brand_id: int
    primary_brand_name: str
    primary_visibility_score: float
    competitors: list[AnalysisResultResponse] = Field(default_factory=list)
    leading_provider: Optional[str] = None
    score_delta: float = Field(
        default=0.0,
        description="Difference between primary brand score and top competitor score",
    )
