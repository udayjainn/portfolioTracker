from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holding import Holding
from app.models.investor import Investor
from app.models.security import Security


async def get_activity_feed(
    db: AsyncSession,
    country: str | None = None,
    page: int = 1,
    limit: int = 50,
) -> tuple[list[dict], int]:
    query = (
        select(
            Holding.id,
            Holding.change_type,
            Holding.shares_change,
            Holding.shares_change_pct,
            Holding.report_date,
            Holding.value_usd,
            Investor.slug.label("investor_slug"),
            Investor.name.label("investor_name"),
            Investor.photo_url.label("investor_photo"),
            Security.ticker,
            Security.name.label("security_name"),
        )
        .join(Investor, Holding.investor_id == Investor.id)
        .join(Security, Holding.security_id == Security.id)
        .where(Holding.change_type != "UNCHANGED")
    )

    if country:
        query = query.where(Investor.country == country)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Holding.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    return [dict(row._mapping) for row in result.all()], total


async def compare_investors(
    db: AsyncSession,
    investor_ids: list[int],
    report_date=None,
) -> dict:
    holdings_by_investor = {}

    for inv_id in investor_ids:
        query = (
            select(Holding)
            .where(Holding.investor_id == inv_id)
            .where(Holding.change_type != "SOLD")
        )
        if report_date:
            query = query.where(Holding.report_date == report_date)
        else:
            latest = select(func.max(Holding.report_date)).where(Holding.investor_id == inv_id)
            query = query.where(Holding.report_date == latest.scalar_subquery())

        result = await db.execute(query)
        holdings_by_investor[inv_id] = {h.security_id for h in result.scalars().all()}

    all_security_ids = set()
    for sids in holdings_by_investor.values():
        all_security_ids |= sids

    overlap = all_security_ids.copy()
    for sids in holdings_by_investor.values():
        overlap &= sids

    unique_to_each: dict[int, list[int]] = {}
    for inv_id, sids in holdings_by_investor.items():
        unique_to_each[inv_id] = list(sids - overlap)

    all_ids = list(overlap | set().union(*unique_to_each.values()))
    securities_by_id: dict[int, Security] = {}
    if all_ids:
        sec_result = await db.execute(select(Security).where(Security.id.in_(all_ids)))
        securities_by_id = {s.id: s for s in sec_result.scalars().all()}

    def _summarize(sec_id: int) -> dict:
        s = securities_by_id.get(sec_id)
        if not s:
            return {"id": sec_id, "ticker": None, "name": None}
        return {"id": s.id, "ticker": s.ticker, "name": s.name}

    return {
        "overlap": [_summarize(sid) for sid in overlap],
        "unique_to_each": {
            str(inv_id): [_summarize(sid) for sid in sids]
            for inv_id, sids in unique_to_each.items()
        },
    }
