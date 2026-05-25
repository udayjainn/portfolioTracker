from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class InvestorSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    photo_url: str | None = None
    country: str
    investor_type: str
    firm_name: str | None = None
    net_worth_usd: int | None = None
    total_holdings_value: Decimal | None = None
    positions_count: int | None = None


class SnapshotSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_date: date
    total_value_usd: Decimal | None = None
    total_positions: int | None = None


class InvestorDetail(InvestorSummary):
    bio: str | None = None
    latest_filing_date: date | None = None
    top_holdings: list = []
    sector_breakdown: dict[str, float] = {}
    portfolio_history: list[SnapshotSummary] = []
