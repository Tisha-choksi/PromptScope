from fastapi import APIRouter

from app.api.v1 import brands, prompts, jobs, analytics

api_router = APIRouter()

api_router.include_router(brands.router, prefix="/brands", tags=["brands"])
api_router.include_router(prompts.router, prefix="/prompts", tags=["prompts"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
