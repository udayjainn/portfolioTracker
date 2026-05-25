from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.holding import Holding
from app.models.investor import Investor
from app.models.security import Security


async def get_holdings_for_investor(
    db: AsyncSession,
    investor_id: int,
    report_date: date | None = None,
    change_type: str | None = None,
    sort: str = "-value_usd",
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Holding], int]:
    query = (
        select(Holding)
        .options(selectinload(Holding.security))
        .where(Holding.investor_id == investor_id)
    )

    if report_date:
        query = query.where(Holding.report_date == report_date)
    else:
        latest = select(func.max(Holding.report_date)).where(Holding.investor_id == investor_id)
        query = query.where(Holding.report_date == latest.scalar_subquery())

    if change_type:
        query = query.where(Holding.change_type == change_type)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    desc = sort.startswith("-")
    col_name = sort.lstrip("-")
    col = getattr(Holding, col_name, Holding.value_usd)
    query = query.order_by(col.desc() if desc else col.asc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_holding_history(
    db: AsyncSession,
    investor_id: int,
    security_id: int,
    periods: int = 8,
) -> list[Holding]:
    result = await db.execute(
        select(Holding)
        .where(Holding.investor_id == investor_id)
        .where(Holding.security_id == security_id)
        .order_by(Holding.report_date.desc())
        .limit(periods)
    )
    return list(result.scalars().all())


async def get_holders_for_security(
    db: AsyncSession,
    security_id: int,
    sort: str = "-value_usd",
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Holding], int]:
    latest = select(func.max(Holding.report_date)).where(Holding.security_id == security_id)

    query = (
        select(Holding)
        .options(selectinload(Holding.investor))
        .where(Holding.security_id == security_id)
        .where(Holding.report_date == latest.scalar_subquery())
        .where(Holding.change_type != "SOLD")
    )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    desc = sort.startswith("-")
    col_name = sort.lstrip("-")
    col = getattr(Holding, col_name, Holding.value_usd)
    query = query.order_by(col.desc() if desc else col.asc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_most_bought(
    db: AsyncSession,
    country: str | None = None,
    limit: int = 20,
) -> list[dict]:
    query = (
        select(
            Security.id,
            Security.ticker,
            Security.name,
            func.count(Holding.id).label("buy_count"),
            func.sum(Holding.value_usd).label("total_value_added"),
        )
        .join(Holding, Holding.security_id == Security.id)
        .where(Holding.change_type.in_(["NEW", "INCREASED"]))
        .group_by(Security.id)
        .order_by(func.count(Holding.id).desc())
        .limit(limit)
    )
    if country:
        query = query.where(Security.country == country)

    result = await db.execute(query)
    return [dict(row._mapping) for row in result.all()]


async def get_most_sold(
    db: AsyncSession,
    country: str | None = None,
    limit: int = 20,
) -> list[dict]:
    query = (
        select(
            Security.id,
            Security.ticker,
            Security.name,
            func.count(Holding.id).label("sell_count"),
            func.sum(Holding.value_usd).label("total_value_removed"),
        )
        .join(Holding, Holding.security_id == Security.id)
        .where(Holding.change_type.in_(["SOLD", "DECREASED"]))
        .group_by(Security.id)
        .order_by(func.count(Holding.id).desc())
        .limit(limit)
    )
    if country:
        query = query.where(Security.country == country)

    result = await db.execute(query)
    return [dict(row._mapping) for row in result.all()]
