from pydantic import BaseModel, ConfigDict


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str | None = None
    avatar_url: str | None = None
    country: str | None = None
    plan: str
    preferences: dict


class UserUpdate(BaseModel):
    display_name: str | None = None
    country: str | None = None
    preferences: dict | None = None
