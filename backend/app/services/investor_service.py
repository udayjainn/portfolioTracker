from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.holding import Holding
from app.models.holding_snapshot import HoldingSnapshot
from app.models.investor import Investor


async def get_investors(
    db: AsyncSession,
    country: str | None = None,
    investor_type: str | None = None,
    sort: str = "-net_worth_usd",
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Investor], int]:
    query = select(Investor).where(Investor.is_active.is_(True))

    if country:
        query = query.where(Investor.country == country)
    if investor_type:
        query = query.where(Investor.investor_type == investor_type)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    desc = sort.startswith("-")
    col_name = sort.lstrip("-")
    col = getattr(Investor, col_name, Investor.name)
    query = query.order_by(col.desc() if desc else col.asc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_investor_by_slug(db: AsyncSession, slug: str) -> Investor | None:
    result = await db.execute(select(Investor).where(Investor.slug == slug))
    return result.scalar_one_or_none()


async def get_trending_investors(
    db: AsyncSession,
    country: str | None = None,
    limit: int = 10,
) -> list[Investor]:
    query = (
        select(Investor)
        .join(Holding, Holding.investor_id == Investor.id)
        .where(Investor.is_active.is_(True))
        .where(Holding.change_type.in_(["NEW", "INCREASED", "SOLD"]))
        .group_by(Investor.id)
        .order_by(func.count(Holding.id).desc())
        .limit(limit)
    )
    if country:
        query = query.where(Investor.country == country)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_investor_snapshot(db: AsyncSession, investor_id: int) -> HoldingSnapshot | None:
    result = await db.execute(
        select(HoldingSnapshot)
        .where(HoldingSnapshot.investor_id == investor_id)
        .order_by(HoldingSnapshot.report_date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_portfolio_history(
    db: AsyncSession,
    investor_id: int,
    periods: int = 8,
) -> list[HoldingSnapshot]:
    result = await db.execute(
        select(HoldingSnapshot)
        .where(HoldingSnapshot.investor_id == investor_id)
        .order_by(HoldingSnapshot.report_date.desc())
        .limit(periods)
    )
    return list(result.scalars().all())
