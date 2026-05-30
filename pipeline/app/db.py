"""Async database access for the pipeline (uses backend models via compose volume mount)."""

from contextlib import asynccontextmanager

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.models.investor import Investor


@asynccontextmanager
async def session_scope():
    """New engine per run — safe inside Celery prefork workers."""
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool, pool_pre_ping=True)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def get_tracked_us_investors(session: AsyncSession) -> list[Investor]:
    result = await session.execute(
        select(Investor)
        .where(Investor.country == "US")
        .where(Investor.is_active.is_(True))
        .where(Investor.firm_cik.isnot(None))
        .order_by(Investor.id)
    )
    return list(result.scalars().all())
