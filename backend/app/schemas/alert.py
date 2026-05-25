from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_type: str
    investor_id: int | None = None
    security_id: int | None = None
    threshold_pct: Decimal | None = None
    channels: list[str]
    is_active: bool
    created_at: datetime


class AlertCreate(BaseModel):
    alert_type: str
    investor_id: int | None = None
    security_id: int | None = None
    threshold_pct: Decimal | None = None
    channels: list[str] = ["push"]


class AlertUpdate(BaseModel):
    threshold_pct: Decimal | None = None
    channels: list[str] | None = None
    is_active: bool | None = None
