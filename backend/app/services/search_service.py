from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.investor import Investor
from app.models.security import Security


async def search(
    db: AsyncSession,
    query: str,
    search_type: str = "investor,security",
    limit: int = 10,
) -> dict:
    results = {"investors": [], "securities": []}
    types = search_type.split(",")
    pattern = f"%{query}%"

    if "investor" in types:
        stmt = (
            select(Investor)
            .where(
                or_(
                    Investor.name.ilike(pattern),
                    Investor.firm_name.ilike(pattern),
                    Investor.slug.ilike(pattern),
                )
            )
            .where(Investor.is_active.is_(True))
            .limit(limit)
        )
        result = await db.execute(stmt)
        results["investors"] = list(result.scalars().all())

    if "security" in types:
        stmt = (
            select(Security)
            .where(
                or_(
                    Security.ticker.ilike(pattern),
                    Security.name.ilike(pattern),
                )
            )
            .where(Security.is_active.is_(True))
            .limit(limit)
        )
        result = await db.execute(stmt)
        results["securities"] = list(result.scalars().all())

    return results


async def autocomplete(
    db: AsyncSession,
    query: str,
    limit: int = 5,
) -> list[str]:
    pattern = f"%{query}%"

    investor_names = await db.execute(
        select(Investor.name)
        .where(Investor.name.ilike(pattern))
        .where(Investor.is_active.is_(True))
        .limit(limit)
    )
    security_names = await db.execute(
        select(Security.name)
        .where(
            or_(
                Security.ticker.ilike(pattern),
                Security.name.ilike(pattern),
            )
        )
        .where(Security.is_active.is_(True))
        .limit(limit)
    )

    names = [row[0] for row in investor_names.all()]
    names.extend(row[0] for row in security_names.all())
    return names[:limit]
