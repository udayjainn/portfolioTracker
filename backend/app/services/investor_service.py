from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.holding import Holding
from app.models.holding_snapshot import HoldingSnapshot
from app.models.investor import Investor

# UI aliases from early scaffold → snapshot / model fields
_SORT_ALIASES = {
    "portfolio_value": "total_value_usd",
    "holdings_count": "total_positions",
}


def _latest_snapshot_scalar(column: str):
    col = getattr(HoldingSnapshot, column)
    return (
        select(col)
        .where(HoldingSnapshot.investor_id == Investor.id)
        .order_by(HoldingSnapshot.report_date.desc())
        .limit(1)
        .correlate(Investor)
        .scalar_subquery()
    )


def _resolve_sort(sort: str) -> tuple[bool, str]:
    raw = sort.lstrip("-")
    desc = sort.startswith("-")
    col_name = _SORT_ALIASES.get(raw, raw)
    if raw in _SORT_ALIASES and not sort.startswith("-"):
        desc = True
    return desc, col_name


async def get_investors(
    db: AsyncSession,
    country: str | None = None,
    investor_type: str | None = None,
    sort: str = "-total_value_usd",
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

    desc, col_name = _resolve_sort(sort)
    if col_name in ("total_value_usd", "total_positions"):
        order_expr = _latest_snapshot_scalar(col_name)
        query = query.order_by(order_expr.desc().nulls_last() if desc else order_expr.asc().nulls_last())
    elif hasattr(Investor, col_name):
        col = getattr(Investor, col_name)
        query = query.order_by(col.desc() if desc else col.asc())
    else:
        query = query.order_by(Investor.name.asc())

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


async def attach_latest_snapshots(
    db: AsyncSession, investors: list[Investor]
) -> dict[int, HoldingSnapshot]:
    if not investors:
        return {}
    ids = [i.id for i in investors]
    subq = (
        select(
            HoldingSnapshot.investor_id,
            func.max(HoldingSnapshot.report_date).label("max_date"),
        )
        .where(HoldingSnapshot.investor_id.in_(ids))
        .group_by(HoldingSnapshot.investor_id)
        .subquery()
    )
    result = await db.execute(
        select(HoldingSnapshot)
        .join(
            subq,
            (HoldingSnapshot.investor_id == subq.c.investor_id)
            & (HoldingSnapshot.report_date == subq.c.max_date),
        )
    )
    return {s.investor_id: s for s in result.scalars().all()}


def investor_to_summary(investor: Investor, snapshot: HoldingSnapshot | None = None) -> dict:
    return {
        "id": investor.id,
        "slug": investor.slug,
        "name": investor.name,
        "photo_url": investor.photo_url,
        "country": investor.country,
        "investor_type": investor.investor_type,
        "firm_name": investor.firm_name,
        "net_worth_usd": investor.net_worth_usd,
        "total_holdings_value": snapshot.total_value_usd if snapshot else None,
        "positions_count": snapshot.total_positions if snapshot else None,
    }


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
