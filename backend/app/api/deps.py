from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.cache.redis_cache import get_cache
from app.services.llm.orchestrator import LLMOrchestrator

# Singleton orchestrator — instantiated once at first use and reused across requests.
_orchestrator: LLMOrchestrator | None = None


def get_orchestrator() -> LLMOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = LLMOrchestrator()
    return _orchestrator
