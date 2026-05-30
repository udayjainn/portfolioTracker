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
            if identifier_type == "CUSIP":
                clean_name = (name or "").strip()
                if clean_name and clean_name.lower() != "unknown":
                    if security.name.startswith("Unknown"):
                        security.name = clean_name[:255]
                if ticker:
                    ticker_upper = ticker.upper()[:20]
                    if security.exchange == "UNKNOWN" or security.ticker == security.cusip:
                        security.ticker = ticker_upper
                        security.exchange = "US"
            return security.id

        if identifier_type == "CUSIP":
            clean_name = (name or "").strip()
            has_ticker = bool(ticker and ticker.strip())
            display_ticker = ticker.upper()[:20] if has_ticker else "UNRESOLVED"
            if clean_name and clean_name.lower() != "unknown":
                display_name = clean_name[:255]
            else:
                display_name = f"Unknown ({identifier})"
            new_security = Security(
                ticker=display_ticker,
                name=display_name,
                cusip=identifier,
                exchange="US" if has_ticker else "UNKNOWN",
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
