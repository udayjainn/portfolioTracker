from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.exceptions import BadRequestException
from app.models.investor import Investor
from app.services import analytics_service

router = APIRouter(prefix="/compare", tags=["compare"])


@router.get("")
async def compare_investors(
    investors: str = Query(..., description="Comma-separated investor slugs"),
    report_date: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    slugs = [s.strip() for s in investors.split(",") if s.strip()]
    if len(slugs) < 2:
        raise BadRequestException("At least 2 investors required")
    if len(slugs) > 4:
        raise BadRequestException("Maximum 4 investors allowed")

    result = await db.execute(select(Investor).where(Investor.slug.in_(slugs)))
    investor_list = list(result.scalars().all())
    if len(investor_list) != len(slugs):
        raise BadRequestException("One or more investor slugs not found")

    comparison = await analytics_service.compare_investors(
        db, [i.id for i in investor_list], report_date
    )
    comparison["investors"] = [
        {"id": i.id, "slug": i.slug, "name": i.name} for i in investor_list
    ]
    return comparison
