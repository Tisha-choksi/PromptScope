"""
main.py
=======
FastAPI application entry point for PromptScope.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # ---- startup --------------------------------------------------------
    try:
        await init_db()
        logger.info("Database tables created/verified.")
    except Exception as exc:
        logger.warning(
            "Could not connect to database on startup: %s. "
            "Check DATABASE_URL in your .env file. "
            "API endpoints that require the DB will return 503 until it is reachable.",
            exc,
        )

    try:
        from app.workers.scheduler import setup_scheduler
        await setup_scheduler()
    except Exception as exc:
        logger.warning("Scheduler could not start: %s", exc)

    yield

    # ---- shutdown -------------------------------------------------------
    from app.workers.scheduler import shutdown_scheduler
    await shutdown_scheduler()


settings = get_settings()

app = FastAPI(
    title="PromptScope",
    description="AI Visibility Monitoring Platform — track how your brand appears across LLM responses.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://frontend:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

from app.api.v1.router import api_router  # noqa: E402 — imported after app creation

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Liveness probe endpoint."""
    return {"status": "ok", "service": "PromptScope"}
