from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.firebase import ensure_firebase
from app.database import get_db
from app.models.user import User


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise UnauthorizedException("Invalid authorization header")

    token = authorization.removeprefix("Bearer ")

    try:
        ensure_firebase()
        import firebase_admin.auth as firebase_auth

        decoded = firebase_auth.verify_id_token(token)
    except Exception:
        raise UnauthorizedException("Invalid or expired token")

    firebase_uid = decoded["uid"]

    result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            firebase_uid=firebase_uid,
            email=decoded.get("email", ""),
            display_name=decoded.get("name"),
            avatar_url=decoded.get("picture"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


async def get_optional_user(
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if not authorization:
        return None
    try:
        return await get_current_user(authorization=authorization, db=db)
    except UnauthorizedException:
        return None
