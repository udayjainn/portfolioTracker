"""Shared helpers for 13F ingest (edgartools + SEC bulk)."""

from datetime import date
from decimal import Decimal


def normalize_cik(cik: str | int | None) -> str | None:
    if cik is None:
        return None
    digits = "".join(c for c in str(cik) if c.isdigit())
    if not digits:
        return None
    return digits.zfill(10)


def holding_row(
    *,
    cusip: str,
    name: str,
    shares: int,
    value_usd: Decimal,
    option_type: str | None = None,
) -> dict:
    return {
        "cusip": cusip.strip().upper(),
        "name": name.strip(),
        "shares": int(shares),
        "value_usd": value_usd,
        "option_type": option_type,
        "sector": "Unknown",
        "country": "US",
    }


def bulk_value_to_usd(value_raw: str | int, report_date: date) -> Decimal:
    """SEC bulk VALUE: dollars since 2023-01-03, thousands before."""
    amount = Decimal(str(value_raw or 0))
    if report_date < date(2023, 1, 3):
        return amount * 1000
    return amount
