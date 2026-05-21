from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.analysis import AnalysisResult, BrandMention


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    aliases: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_competitor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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
    mentions: Mapped[list["BrandMention"]] = relationship(
        "BrandMention", back_populates="brand", cascade="all, delete-orphan"
    )
    analysis_results: Mapped[list["AnalysisResult"]] = relationship(
        "AnalysisResult", back_populates="brand", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Brand id={self.id} name={self.name!r}>"
