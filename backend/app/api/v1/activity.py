from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services import analytics_service
from app.utils.pagination import build_paginated_response

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("/feed")
async def activity_feed(
    country: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items, total = await analytics_service.get_activity_feed(
        db, country=country, page=page, limit=limit
    )
    return build_paginated_response(items, total, page, limit)
