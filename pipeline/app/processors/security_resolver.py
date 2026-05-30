from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.security import Security


class SecurityResolver:
    async def resolve(
        self,
        identifier: str,
        identifier_type: str,
        db,
        *,
        ticker: str | None = None,
        name: str | None = None,
    ) -> int | None:
        if identifier_type == "CUSIP":
            result = await db.execute(select(Security).where(Security.cusip == identifier))
        elif identifier_type == "ISIN":
            result = await db.execute(select(Security).where(Security.isin == identifier))
        elif identifier_type == "TICKER":
            result = await db.execute(select(Security).where(Security.ticker == identifier.upper()))
        else:
            return None

        security = result.scalar_one_or_none()
        if security:
            return security.id

        if identifier_type == "CUSIP":
            display_ticker = (ticker or identifier).upper()[:20]
            display_name = name or f"Unknown ({identifier})"
            new_security = Security(
                ticker=display_ticker,
                name=display_name[:255],
                cusip=identifier,
                exchange="US" if ticker else "UNKNOWN",
                country="US",
            )
            db.add(new_security)
            try:
                await db.flush()
                await db.refresh(new_security)
                return new_security.id
            except IntegrityError:
                await db.rollback()
                retry = await db.execute(select(Security).where(Security.cusip == identifier))
                existing = retry.scalar_one_or_none()
                return existing.id if existing else None

        return None
