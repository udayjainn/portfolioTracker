from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SecuritySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    name: str
    exchange: str
    country: str
    sector: str | None = None
    asset_type: str
    current_price: Decimal | None = None
    market_cap_usd: int | None = None
    currency: str


class SecurityDetail(SecuritySummary):
    industry: str | None = None
    isin: str | None = None
    cusip: str | None = None
    sedol: str | None = None
