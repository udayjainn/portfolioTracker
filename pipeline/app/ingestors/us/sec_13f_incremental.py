"""Daily incremental 13F ingest via edgartools (per seeded CIK)."""

import asyncio
import logging
import time
from datetime import date
from decimal import Decimal

from app.config import settings
from app.db import get_tracked_us_investors, session_scope
from app.ingestors.us.thirteen_f_common import holding_row, normalize_cik
from app.processors.filing_processor import FilingProcessor

logger = logging.getLogger(__name__)


def _configure_edgar() -> None:
    from edgar import set_identity

    set_identity(f"PortfolioTracker/1.0 ({settings.CONTACT_EMAIL})")


def _col(row, *names: str, default=None):
    for name in names:
        if name in row.index:
            return row[name]
        for col in row.index:
            if str(col).lower() == name.lower():
                return row[col]
    return default


def _fetch_latest_13f(cik: str) -> dict | None:
    from edgar import Company

    company = Company(int(cik))
    filings = company.get_filings(form="13F-HR")
    if not filings or len(filings) == 0:
        return None

    filing = filings[0]
    report = filing.obj()
    holdings_df = report.holdings
    if holdings_df is None or holdings_df.empty:
        return None

    report_date = getattr(report, "report_period", None) or getattr(report, "period_of_report", None)
    if hasattr(report_date, "date"):
        report_date = report_date.date()
    elif isinstance(report_date, str):
        report_date = date.fromisoformat(report_date[:10])

    filing_date = getattr(filing, "filing_date", None) or getattr(filing, "filed_date", None)
    if hasattr(filing_date, "date"):
        filing_date = filing_date.date()
    elif isinstance(filing_date, str):
        filing_date = date.fromisoformat(filing_date[:10])
    else:
        filing_date = report_date

    parsed = []
    for _, row in holdings_df.iterrows():
        cusip = str(_col(row, "Cusip", "cusip", "CUSIP", default="")).strip()
        if not cusip or cusip.lower() == "nan":
            continue
        name = str(_col(row, "Issuer", "nameOfIssuer", "Name", default="Unknown"))
        shares_raw = _col(row, "SharesPrnAmount", "Shares", "sshPrnamt", "ShrsOrPrnAmt", default=0) or 0
        shares = int(float(shares_raw))
        value_usd = Decimal(str(_col(row, "Value", "value", default=0) or 0))
        ticker = str(_col(row, "Ticker", "ticker", default="") or "").strip()
        option_type = _col(row, "PutCall", "putCall", default=None)
        if option_type is not None and str(option_type).lower() in ("nan", "none", ""):
            option_type = None
        parsed.append(
            {
                **holding_row(
                    cusip=cusip,
                    name=name,
                    shares=shares,
                    value_usd=value_usd,
                    option_type=str(option_type)[:4] if option_type else None,
                ),
                "ticker": ticker.upper() if ticker and ticker.lower() != "nan" else None,
            }
        )

    return {
        "report_date": report_date,
        "filing_date": filing_date,
        "filing_url": getattr(filing, "filing_url", None) or getattr(filing, "url", None),
        "accession": getattr(filing, "accession_number", None),
        "holdings": parsed,
        "raw_data": {
            "source": "edgartools",
            "accession": getattr(filing, "accession_number", None),
            "holdings_count": len(parsed),
        },
    }


async def run_incremental_ingest(*, limit: int | None = None, force_reprocess: bool = False) -> dict:
    _configure_edgar()
    processor = FilingProcessor()
    stats = {"processed": 0, "skipped": 0, "failed": 0, "errors": []}

    async with session_scope() as session:
        investors = await get_tracked_us_investors(session)
        if limit:
            investors = investors[:limit]

        for investor in investors:
            cik = normalize_cik(investor.firm_cik)
            if not cik:
                stats["skipped"] += 1
                continue
            try:
                payload = await asyncio.to_thread(_fetch_latest_13f, cik)
                if not payload:
                    stats["skipped"] += 1
                    continue

                filing_id = await processor.process(
                    session,
                    investor_id=investor.id,
                    report_date=payload["report_date"],
                    filing_date=payload["filing_date"],
                    filing_url=payload["filing_url"],
                    raw_data=payload["raw_data"],
                    parsed_holdings=payload["holdings"],
                    force_reprocess=force_reprocess,
                )
                if filing_id:
                    stats["processed"] += 1
                else:
                    stats["skipped"] += 1
            except Exception as exc:
                await session.rollback()
                logger.exception("13F incremental failed for %s (%s)", investor.slug, cik)
                stats["failed"] += 1
                stats["errors"].append(f"{investor.slug}: {exc}")
            time.sleep(0.12)

    return stats
