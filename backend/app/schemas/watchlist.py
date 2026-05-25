from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WatchlistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_type: str
    investor_id: int | None = None
    security_id: int | None = None
    created_at: datetime


class WatchlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    items: list[WatchlistItemResponse] = []
    created_at: datetime


class WatchlistCreate(BaseModel):
    name: str = "Default"


class WatchlistItemCreate(BaseModel):
    item_type: str
    investor_id: int | None = None
    security_id: int | None = None
