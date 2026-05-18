import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.analysis import BrandMention
from app.models.brand import Brand
from app.schemas.brand import BrandCreate, BrandResponse, BrandUpdate
from app.schemas.analysis import BrandMentionResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[BrandResponse])
async def list_brands(
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[BrandResponse]:
    """Return a paginated list of brands, optionally filtered by active status."""
    stmt = select(Brand).order_by(Brand.id)
    if is_active is not None:
        stmt = stmt.where(Brand.is_active == is_active)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    payload: BrandCreate,
    db: AsyncSession = Depends(get_db),
) -> BrandResponse:
    """Create a new brand."""
    # Check uniqueness
    existing = await db.execute(select(Brand).where(Brand.name == payload.name))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Brand with name '{payload.name}' already exists.",
        )
    brand = Brand(**payload.model_dump())
    db.add(brand)
    await db.flush()
    await db.refresh(brand)
    return brand


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: int,
    db: AsyncSession = Depends(get_db),
) -> BrandResponse:
    """Retrieve a single brand by ID."""
    brand = await _get_brand_or_404(brand_id, db)
    return brand


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: int,
    payload: BrandUpdate,
    db: AsyncSession = Depends(get_db),
) -> BrandResponse:
    """Update a brand's fields."""
    brand = await _get_brand_or_404(brand_id, db)

    # Check name uniqueness if name is being changed
    if payload.name is not None and payload.name != brand.name:
        existing = await db.execute(select(Brand).where(Brand.name == payload.name))
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Brand with name '{payload.name}' already exists.",
            )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(brand, field, value)

    await db.flush()
    await db.refresh(brand)
    return brand


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(
    brand_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete a brand by setting is_active=False."""
    brand = await _get_brand_or_404(brand_id, db)
    brand.is_active = False
    await db.flush()


@router.get("/{brand_id}/mentions", response_model=list[BrandMentionResponse])
async def get_brand_mentions(
    brand_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[BrandMentionResponse]:
    """Return recent mentions for a brand from the last 30 days, paginated."""
    await _get_brand_or_404(brand_id, db)

    since = datetime.now(tz=timezone.utc) - timedelta(days=30)
    stmt = (
        select(BrandMention)
        .where(BrandMention.brand_id == brand_id)
        .where(BrandMention.created_at >= since)
        .order_by(BrandMention.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _get_brand_or_404(brand_id: int, db: AsyncSession) -> Brand:
    result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = result.scalar_one_or_none()
    if brand is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand {brand_id} not found.",
        )
    return brand
