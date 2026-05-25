from datetime import date

from pydantic import BaseModel, ConfigDict


class FilingSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    investor_id: int
    filing_type: str
    source_country: str
    filing_date: date
    report_date: date
    status: str


class FilingDetail(FilingSummary):
    filing_url: str | None = None
    raw_data: dict | None = None
