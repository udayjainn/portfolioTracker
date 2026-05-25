from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services import notification_service
from app.utils.pagination import build_paginated_response

router = APIRouter(prefix="/notifications", tags=["notifications"])


class MarkReadRequest(BaseModel):
    ids: list[int]


@router.get("")
async def list_notifications(
    is_read: bool | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notifications, total = await notification_service.get_notifications(
        db, user.id, is_read=is_read, page=page, limit=limit
    )
    return build_paginated_response(
        [
            {
                "id": n.id,
                "title": n.title,
                "body": n.body,
                "notification_type": n.notification_type,
                "payload": n.payload,
                "is_read": n.is_read,
                "created_at": str(n.created_at),
            }
            for n in notifications
        ],
        total,
        page,
        limit,
    )


@router.post("/mark-read")
async def mark_read(
    data: MarkReadRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await notification_service.mark_as_read(db, user.id, data.ids)
    return {"status": "ok"}
