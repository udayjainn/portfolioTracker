"""Quarterly SEC Form 13F bulk ZIP ingest for seeded CIKs."""

import csv
import io
import logging
import zipfile
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx

from app.config import settings
from app.db import get_tracked_us_investors, session_scope
from app.ingestors.us.thirteen_f_common import bulk_value_to_usd, holding_row, normalize_cik
from app.processors.filing_processor import FilingProcessor

logger = logging.getLogger(__name__)

SEC_HEADERS = {"User-Agent": f"PortfolioTracker/1.0 ({settings.CONTACT_EMAIL})"}


def _read_tsv(text: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    return [{k.upper(): (v or "").strip() for k, v in row.items() if k} for row in reader]


def _find_column(row: dict, *candidates: str) -> str | None:
    for key in row:
        if key.upper() in {c.upper() for c in candidates}:
            return row.get(key) or None
    return None


def _build_accession_cik_map(rows: list[dict]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in rows:
        accession = _find_column(row, "ACCESSION_NUMBER")
        cik = _find_column(row, "CIK", "CIK_NUMBER", "FILER_CI")
        if accession and cik:
            mapping[accession] = normalize_cik(cik) or cik
    return mapping


def _parse_bulk_zip(zip_bytes: bytes, tracked_ciks: set[str]) -> dict[str, list[dict]]:
    """Return {cik: [holding_row dicts grouped by accession — latest accession per cik wins]."""
    by_cik_accession: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    accession_dates: dict[str, date] = {}

    with TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "bulk.zip"
        zpath.write_bytes(zip_bytes)
        with zipfile.ZipFile(zpath) as zf:
            names = zf.namelist()
            submission_rows: list[dict] = []
            cover_rows: list[dict] = []
            infotable_rows: list[dict] = []

            for name in names:
                if not name.lower().endswith(".tsv"):
                    continue
                content = zf.read(name).decode("utf-8", errors="replace")
                rows = _read_tsv(content)
                upper_name = name.upper()
                if "SUBMISSION" in upper_name:
                    submission_rows = rows
                elif "COVERPAGE" in upper_name:
                    cover_rows = rows
                elif "INFOTABLE" in upper_name:
                    infotable_rows = rows

            accession_to_cik = _build_accession_cik_map(submission_rows)
            if not accession_to_cik and cover_rows:
                accession_to_cik = _build_accession_cik_map(cover_rows)

            for row in infotable_rows:
                accession = _find_column(row, "ACCESSION_NUMBER")
                cik = accession_to_cik.get(accession or "")
                if not cik or cik not in tracked_ciks:
                    continue

                cusip = _find_column(row, "CUSIP")
                if not cusip:
                    continue

                report_date_str = _find_column(row, "REPORTCALENDARORQUARTER", "PERIOD_OF_REPORT")
                report_date = date.today()
                if report_date_str and len(report_date_str) >= 10:
                    try:
                        report_date = date.fromisoformat(report_date_str[:10])
                    except ValueError:
                        pass
                accession_dates[accession] = report_date

                value_usd = bulk_value_to_usd(
                    _find_column(row, "VALUE", default="0") or "0",
                    report_date,
                )
                shares = int(float(_find_column(row, "SSHPRNAMT", default="0") or 0))
                name = _find_column(row, "NAMEOFISSUER", default="Unknown") or "Unknown"
                option_type = _find_column(row, "PUTCALL")

                by_cik_accession[cik][accession].append(
                    holding_row(
                        cusip=cusip,
                        name=name,
                        shares=shares,
                        value_usd=value_usd,
                        option_type=option_type[:4] if option_type else None,
                    )
                )

    result: dict[str, dict] = {}
    for cik, accessions in by_cik_accession.items():
        if not accessions:
            continue
        latest_accession = max(accessions.keys())
        result[cik] = {
            "holdings": accessions[latest_accession],
            "report_date": accession_dates.get(latest_accession, date.today()),
            "filing_date": date.today(),
        }
    return result


async def run_bulk_ingest(*, zip_url: str | None = None) -> dict:
    url = zip_url or settings.SEC_13F_BULK_URL
    stats = {"processed": 0, "skipped": 0, "failed": 0, "errors": []}
    processor = FilingProcessor()

    async with httpx.AsyncClient(timeout=120.0, headers=SEC_HEADERS) as client:
        response = await client.get(url)
        response.raise_for_status()
        zip_bytes = response.content

    async with session_scope() as session:
        investors = await get_tracked_us_investors(session)
        cik_to_investor = {normalize_cik(i.firm_cik): i for i in investors if normalize_cik(i.firm_cik)}
        tracked = set(cik_to_investor.keys())
        holdings_by_cik = _parse_bulk_zip(zip_bytes, tracked)

        for cik, bundle in holdings_by_cik.items():
            investor = cik_to_investor.get(cik)
            holdings = bundle.get("holdings", [])
            if not investor or not holdings:
                stats["skipped"] += 1
                continue
            try:
                report_date = bundle["report_date"]
                filing_date = bundle.get("filing_date", report_date)
                filing_id = await processor.process(
                    session,
                    investor_id=investor.id,
                    report_date=report_date,
                    filing_date=filing_date,
                    filing_url=f"bulk:{url}",
                    raw_data={"source": "sec_bulk", "zip_url": url, "holdings_count": len(holdings)},
                    parsed_holdings=holdings,
                )
                if filing_id:
                    stats["processed"] += 1
                else:
                    stats["skipped"] += 1
            except Exception as exc:
                logger.exception("Bulk 13F failed for %s", investor.slug)
                stats["failed"] += 1
                stats["errors"].append(f"{investor.slug}: {exc}")

    return stats
