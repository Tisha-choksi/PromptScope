from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.job import MonitoringJob


class PromptCategory(str, Enum):
    PRODUCT_RECOMMENDATION = "product_recommendation"
    BRAND_AWARENESS = "brand_awareness"
    COMPETITOR_COMPARISON = "competitor_comparison"
    FEATURE_INQUIRY = "feature_inquiry"
    GENERAL = "general"


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[PromptCategory] = mapped_column(
        String(64), nullable=False, default=PromptCategory.GENERAL
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    schedule_cron: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    target_brands: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    jobs: Mapped[list["MonitoringJob"]] = relationship(
        "MonitoringJob", back_populates="prompt", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Prompt id={self.id} category={self.category!r}>"
