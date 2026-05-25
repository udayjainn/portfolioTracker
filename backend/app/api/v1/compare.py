from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.investor import Investor
from app.services import analytics_service

router = APIRouter(prefix="/compare", tags=["compare"])


@router.get("")
async def compare_investors(
    investors: str = Query(..., description="Comma-separated investor slugs"),
    report_date: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    slugs = [s.strip() for s in investors.split(",")]
    result = await db.execute(select(Investor).where(Investor.slug.in_(slugs)))
    investor_list = list(result.scalars().all())
    investor_ids = [i.id for i in investor_list]

    comparison = await analytics_service.compare_investors(db, investor_ids, report_date)
    return comparison
