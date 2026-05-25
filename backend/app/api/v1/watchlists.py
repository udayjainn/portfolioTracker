from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.models.watchlist import Watchlist, WatchlistItem
from app.schemas.watchlist import WatchlistCreate, WatchlistItemCreate, WatchlistResponse

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


@router.get("", response_model=list[WatchlistResponse])
async def list_watchlists(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Watchlist)
        .options(selectinload(Watchlist.items))
        .where(Watchlist.user_id == user.id)
    )
    return [WatchlistResponse.model_validate(w) for w in result.scalars().all()]


@router.post("", response_model=WatchlistResponse)
async def create_watchlist(
    data: WatchlistCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    watchlist = Watchlist(user_id=user.id, name=data.name)
    db.add(watchlist)
    await db.commit()
    await db.refresh(watchlist)
    return WatchlistResponse.model_validate(watchlist)


@router.delete("/{watchlist_id}")
async def delete_watchlist(
    watchlist_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Watchlist).where(Watchlist.id == watchlist_id, Watchlist.user_id == user.id)
    )
    watchlist = result.scalar_one_or_none()
    if not watchlist:
        raise NotFoundException("Watchlist not found")
    await db.delete(watchlist)
    await db.commit()
    return {"status": "deleted"}


@router.post("/{watchlist_id}/items")
async def add_item(
    watchlist_id: int,
    data: WatchlistItemCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Watchlist).where(Watchlist.id == watchlist_id, Watchlist.user_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise NotFoundException("Watchlist not found")

    item = WatchlistItem(
        watchlist_id=watchlist_id,
        item_type=data.item_type,
        investor_id=data.investor_id,
        security_id=data.security_id,
    )
    db.add(item)
    await db.commit()
    return {"status": "added"}


@router.delete("/{watchlist_id}/items/{item_id}")
async def remove_item(
    watchlist_id: int,
    item_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Watchlist).where(Watchlist.id == watchlist_id, Watchlist.user_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise NotFoundException("Watchlist not found")

    result = await db.execute(
        select(WatchlistItem).where(WatchlistItem.id == item_id, WatchlistItem.watchlist_id == watchlist_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundException("Item not found")
    await db.delete(item)
    await db.commit()
    return {"status": "removed"}
