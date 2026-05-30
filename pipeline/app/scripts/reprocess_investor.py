"""Re-ingest latest 13F for one investor by slug (refreshes tickers/names from edgartools)."""

import argparse
import asyncio
import logging

from sqlalchemy import select

from app.db import session_scope
from app.ingestors.us.sec_13f_incremental import _configure_edgar, _fetch_latest_13f
from app.ingestors.us.thirteen_f_common import normalize_cik
from app.models.investor import Investor
from app.processors.filing_processor import FilingProcessor

logger = logging.getLogger(__name__)


async def reprocess(slug: str, *, force: bool = True) -> None:
    _configure_edgar()
    processor = FilingProcessor()

    async with session_scope() as session:
        result = await session.execute(select(Investor).where(Investor.slug == slug))
        investor = result.scalar_one_or_none()
        if not investor:
            raise SystemExit(f"Investor not found: {slug}")
        if not investor.firm_cik:
            raise SystemExit(f"No firm_cik for {slug}")

        cik = normalize_cik(investor.firm_cik)
        payload = await asyncio.to_thread(_fetch_latest_13f, cik)
        if not payload:
            raise SystemExit(f"No 13F payload from SEC for {slug} (CIK {cik})")

        filing_id = await processor.process(
            session,
            investor_id=investor.id,
            report_date=payload["report_date"],
            filing_date=payload["filing_date"],
            filing_url=payload["filing_url"],
            raw_data=payload["raw_data"],
            parsed_holdings=payload["holdings"],
            force_reprocess=force,
        )
        if filing_id:
            logger.info("Reprocessed %s filing_id=%s holdings=%s", slug, filing_id, len(payload["holdings"]))
        else:
            logger.info("No changes committed for %s (filing may be unchanged)", slug)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("slug", help="Investor slug, e.g. ken-griffin")
    parser.add_argument("--no-force", action="store_true", help="Skip delete/rebuild if filing exists")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(reprocess(args.slug, force=not args.no_force))


if __name__ == "__main__":
    main()
