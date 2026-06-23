from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.analysis import AnalysisResult
    from app.models.prompt import Prompt
    from app.models.response import LLMResponse


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MonitoringJob(Base):
    __tablename__ = "monitoring_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    prompt_id: Mapped[int] = mapped_column(
        ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[JobStatus] = mapped_column(
        String(32), nullable=False, default=JobStatus.PENDING, index=True
    )
    providers: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    prompt: Mapped["Prompt"] = relationship("Prompt", back_populates="jobs")
    responses: Mapped[list["LLMResponse"]] = relationship(
        "LLMResponse", back_populates="job", cascade="all, delete-orphan"
    )
    analysis_results: Mapped[list["AnalysisResult"]] = relationship(
        "AnalysisResult", back_populates="job", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MonitoringJob id={self.id} status={self.status!r}>"
