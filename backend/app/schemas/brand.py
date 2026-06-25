from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BrandCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    aliases: list[str] = Field(default_factory=list)
    domain: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    is_competitor: bool = False
    is_active: bool = True


class BrandUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    aliases: Optional[list[str]] = None
    domain: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    is_competitor: Optional[bool] = None
    is_active: Optional[bool] = None


class BrandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    aliases: list[str]
    domain: Optional[str]
    description: Optional[str]
    is_competitor: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class BrandWithStats(BrandResponse):
    """BrandResponse extended with aggregated visibility statistics."""

    total_mentions: int = 0
    avg_visibility_score: float = 0.0
    latest_visibility_score: Optional[float] = None
    positive_mention_rate: float = 0.0
    providers_mentioned_in: list[str] = Field(default_factory=list)
