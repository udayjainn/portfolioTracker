from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.security import Security

# Exchange label for CUSIP-only rows (unique per ticker+cusip via ticker=cusip).
CUSIP_EXCHANGE = "CUSIP"


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
                self._maybe_enrich_existing(security, identifier, ticker=ticker, name=name)
            return security.id

        if identifier_type == "CUSIP":
            return await self._create_cusip_security(db, identifier, ticker=ticker, name=name)

        return None

    def _maybe_enrich_existing(
        self,
        security: Security,
        cusip: str,
        *,
        ticker: str | None,
        name: str | None,
    ) -> None:
        clean_name = (name or "").strip()
        if clean_name and clean_name.lower() != "unknown":
            if security.name.startswith("Unknown") or security.name == f"Unknown ({cusip})":
                security.name = clean_name[:255]

        if not ticker or not str(ticker).strip():
            return

        ticker_upper = str(ticker).upper()[:20]
        placeholder = security.exchange in (CUSIP_EXCHANGE, "UNKNOWN") or security.ticker in (
            "UNRESOLVED",
            cusip,
            security.cusip,
        )
        if placeholder:
            security.ticker = ticker_upper
            security.exchange = "US"

    async def _create_cusip_security(
        self,
        db,
        cusip: str,
        *,
        ticker: str | None,
        name: str | None,
    ) -> int | None:
        clean_name = (name or "").strip()
        has_ticker = bool(ticker and str(ticker).strip())
        display_ticker = str(ticker).upper()[:20] if has_ticker else cusip.upper()[:20]
        exchange = "US" if has_ticker else CUSIP_EXCHANGE

        if clean_name and clean_name.lower() != "unknown":
            display_name = clean_name[:255]
        else:
            display_name = f"Unknown ({cusip})"

        new_security = Security(
            ticker=display_ticker,
            name=display_name,
            cusip=cusip,
            exchange=exchange,
            country="US",
        )
        try:
            async with db.begin_nested():
                db.add(new_security)
                await db.flush()
                await db.refresh(new_security)
                return new_security.id
        except IntegrityError:
            retry = await db.execute(select(Security).where(Security.cusip == cusip))
            existing = retry.scalar_one_or_none()
            if existing:
                self._maybe_enrich_existing(existing, cusip, ticker=ticker, name=name)
                return existing.id
            return None
