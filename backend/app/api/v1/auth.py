from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserProfile, UserUpdate

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserProfile)
async def get_me(user: User = Depends(get_current_user)):
    return UserProfile.model_validate(user)


@router.patch("/me", response_model=UserProfile)
async def update_me(
    updates: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if updates.display_name is not None:
        user.display_name = updates.display_name
    if updates.country is not None:
        user.country = updates.country
    if updates.preferences is not None:
        user.preferences = updates.preferences
    await db.commit()
    await db.refresh(user)
    return UserProfile.model_validate(user)


@router.post("/register-device")
async def register_device(
    fcm_token: str,
    platform: str = "web",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.preferences:
        user.preferences = {}
    devices = user.preferences.get("devices", [])
    device_entry = {"fcm_token": fcm_token, "platform": platform}
    if device_entry not in devices:
        devices.append(device_entry)
    user.preferences = {**user.preferences, "devices": devices}
    await db.commit()
    return {"status": "registered"}
