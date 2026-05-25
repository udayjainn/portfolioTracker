from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SecurityBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    name: str
    exchange: str
    asset_type: str


class HoldingSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    security: SecurityBrief
    shares: int
    value_usd: Decimal | None = None
    pct_of_portfolio: Decimal | None = None
    change_type: str
    shares_change: int = 0
    shares_change_pct: Decimal | None = None


class HoldingHistoryPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_date: date
    shares: int
    value_usd: Decimal | None = None
    change_type: str
