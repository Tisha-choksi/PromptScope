from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.prompt import PromptCategory


class PromptCreate(BaseModel):
    text: str = Field(..., min_length=1)
    category: PromptCategory = PromptCategory.GENERAL
    description: Optional[str] = None
    is_active: bool = True
    schedule_cron: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Cron expression for automated scheduling, e.g. '0 * * * *'",
    )
    target_brands: list[int] = Field(
        default_factory=list,
        description="List of brand IDs to track in responses",
    )


class PromptUpdate(BaseModel):
    text: Optional[str] = Field(default=None, min_length=1)
    category: Optional[PromptCategory] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    schedule_cron: Optional[str] = Field(default=None, max_length=128)
    target_brands: Optional[list[int]] = None


class PromptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    category: PromptCategory
    description: Optional[str]
    is_active: bool
    schedule_cron: Optional[str]
    target_brands: list[int]
    created_at: datetime
    updated_at: datetime
