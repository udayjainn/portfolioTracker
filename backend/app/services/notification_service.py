from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def get_notifications(
    db: AsyncSession,
    user_id: int,
    is_read: bool | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Notification], int]:
    query = select(Notification).where(Notification.user_id == user_id)

    if is_read is not None:
        query = query.where(Notification.is_read == is_read)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Notification.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all()), total


async def mark_as_read(db: AsyncSession, user_id: int, notification_ids: list[int]):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id)
        .where(Notification.id.in_(notification_ids))
        .values(is_read=True)
    )
    await db.commit()


async def create_notification(
    db: AsyncSession,
    user_id: int,
    title: str,
    body: str,
    notification_type: str,
    payload: dict | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        body=body,
        notification_type=notification_type,
        payload=payload or {},
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification
