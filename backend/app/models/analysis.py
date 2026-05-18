from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.job import MonitoringJob
    from app.models.response import LLMResponse


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class BrandMention(Base):
    __tablename__ = "brand_mentions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    response_id: Mapped[int] = mapped_column(
        ForeignKey("llm_responses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mention_text: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sentiment: Mapped[SentimentLabel] = mapped_column(
        String(32), nullable=False, default=SentimentLabel.NEUTRAL
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    response: Mapped["LLMResponse"] = relationship("LLMResponse", back_populates="mentions")
    brand: Mapped["Brand"] = relationship("Brand", back_populates="mentions")

    def __repr__(self) -> str:
        return (
            f"<BrandMention id={self.id} brand_id={self.brand_id} "
            f"sentiment={self.sentiment!r}>"
        )


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("monitoring_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mention_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_rank: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    first_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    positive_mentions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    neutral_mentions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    negative_mentions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    visibility_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    providers_mentioned_in: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    job: Mapped["MonitoringJob"] = relationship("MonitoringJob", back_populates="analysis_results")
    brand: Mapped["Brand"] = relationship("Brand", back_populates="analysis_results")

    def __repr__(self) -> str:
        return (
            f"<AnalysisResult id={self.id} brand_id={self.brand_id} "
            f"visibility_score={self.visibility_score:.2f}>"
        )
