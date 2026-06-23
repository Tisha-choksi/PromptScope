from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.job import JobStatus
from app.schemas.analysis import AnalysisResultResponse


class JobCreate(BaseModel):
    prompt_id: int
    providers: list[str] = Field(
        ...,
        min_length=1,
        description="LLM provider identifiers, e.g. ['openai', 'anthropic']",
    )


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt_id: int
    status: JobStatus
    providers: list[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime


class JobWithResults(JobResponse):
    """JobResponse extended with the analysis results produced by the job."""

    analysis_results: list[AnalysisResultResponse] = Field(default_factory=list)
