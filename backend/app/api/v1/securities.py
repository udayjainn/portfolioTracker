from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.exceptions import NotFoundException
from app.models.security import Security
from app.schemas.common import PaginatedResponse
from app.schemas.security import SecurityDetail, SecuritySummary
from app.services import holding_service
from app.utils.pagination import build_paginated_response

router = APIRouter(prefix="/securities", tags=["securities"])


@router.get("", response_model=PaginatedResponse[SecuritySummary])
async def list_securities(
    ticker: str | None = None,
    exchange: str | None = None,
    country: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Security).where(Security.is_active.is_(True))
    if ticker:
        query = query.where(Security.ticker.ilike(f"%{ticker}%"))
    if exchange:
        query = query.where(Security.exchange == exchange)
    if country:
        query = query.where(Security.country == country)

    from sqlalchemy import func

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    securities = list(result.scalars().all())
    return build_paginated_response(
        [SecuritySummary.model_validate(s) for s in securities], total, page, limit
    )


@router.get("/most-bought")
async def most_bought(
    country: str | None = None,
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    return await holding_service.get_most_bought(db, country=country, limit=limit)


@router.get("/most-sold")
async def most_sold(
    country: str | None = None,
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    return await holding_service.get_most_sold(db, country=country, limit=limit)


@router.get("/{ticker}", response_model=SecurityDetail)
async def get_security(ticker: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Security).where(Security.ticker == ticker.upper()).where(Security.is_active.is_(True))
    )
    security = result.scalar_one_or_none()
    if not security:
        raise NotFoundException(f"Security '{ticker}' not found")
    return SecurityDetail.model_validate(security)


@router.get("/{ticker}/holders")
async def get_holders(
    ticker: str,
    sort: str = "-value_usd",
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Security).where(Security.ticker == ticker.upper())
    )
    security = result.scalar_one_or_none()
    if not security:
        raise NotFoundException(f"Security '{ticker}' not found")

    holdings, total = await holding_service.get_holders_for_security(
        db, security.id, sort=sort, page=page, limit=limit
    )
    return build_paginated_response(
        [
            {
                "investor_name": h.investor.name if h.investor else None,
                "investor_slug": h.investor.slug if h.investor else None,
                "shares": h.shares,
                "value_usd": str(h.value_usd) if h.value_usd else None,
                "pct_of_portfolio": str(h.pct_of_portfolio) if h.pct_of_portfolio else None,
                "change_type": h.change_type,
            }
            for h in holdings
        ],
        total,
        page,
        limit,
    )
