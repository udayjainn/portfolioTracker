"""One-off: fix legacy UNRESOLVED/UNKNOWN securities so each CUSIP has a unique (ticker, exchange)."""

import asyncio
import logging

from sqlalchemy import select

from app.db import session_scope
from app.models.security import Security
from app.processors.security_resolver import CUSIP_EXCHANGE

logger = logging.getLogger(__name__)


async def fix() -> None:
    async with session_scope() as session:
        result = await session.execute(
            select(Security).where(
                (Security.ticker == "UNRESOLVED")
                | (Security.exchange == "UNKNOWN")
                | (Security.ticker == Security.cusip)
            )
        )
        rows = list(result.scalars().all())
        updated = 0
        for sec in rows:
            if not sec.cusip:
                continue
            if sec.ticker != sec.cusip.upper()[:20] or sec.exchange != CUSIP_EXCHANGE:
                sec.ticker = sec.cusip.upper()[:20]
                sec.exchange = CUSIP_EXCHANGE
                updated += 1
        await session.commit()
        logger.info("Updated %s securities (%s scanned)", updated, len(rows))


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(fix())


if __name__ == "__main__":
    main()
