"""
main.py
=======
FastAPI application entry point for PromptScope.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler.

    Startup
    -------
    - Create all DB tables (idempotent; does nothing if they already exist).
    - Start the APScheduler background scheduler.

    Shutdown
    --------
    - Gracefully stop the scheduler so in-flight jobs can drain.
    """
    # ---- startup --------------------------------------------------------
    await init_db()

    from app.workers.scheduler import setup_scheduler
    await setup_scheduler()

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
