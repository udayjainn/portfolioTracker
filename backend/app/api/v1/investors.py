from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.exceptions import NotFoundException
from app.schemas.common import PaginatedResponse
from app.schemas.holding import HoldingHistoryPoint, HoldingSummary
from app.schemas.investor import InvestorDetail, InvestorSummary
from app.services import holding_service, investor_service
from app.utils.pagination import build_paginated_response

router = APIRouter(prefix="/investors", tags=["investors"])


@router.get("", response_model=PaginatedResponse[InvestorSummary])
async def list_investors(
    country: str | None = None,
    type: str | None = None,
    sort: str = "-net_worth_usd",
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    investors, total = await investor_service.get_investors(
        db, country=country, investor_type=type, sort=sort, page=page, limit=limit
    )
    snapshots = await investor_service.attach_latest_snapshots(db, investors)
    summaries = [
        InvestorSummary.model_validate(
            investor_service.investor_to_summary(i, snapshots.get(i.id))
        )
        for i in investors
    ]
    return build_paginated_response(summaries, total, page, limit)


@router.get("/trending", response_model=list[InvestorSummary])
async def trending_investors(
    country: str | None = None,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    investors = await investor_service.get_trending_investors(db, country=country, limit=limit)
    snapshots = await investor_service.attach_latest_snapshots(db, investors)
    return [
        InvestorSummary.model_validate(
            investor_service.investor_to_summary(i, snapshots.get(i.id))
        )
        for i in investors
    ]


@router.get("/{slug}", response_model=InvestorDetail)
async def get_investor(slug: str, db: AsyncSession = Depends(get_db)):
    investor = await investor_service.get_investor_by_slug(db, slug)
    if not investor:
        raise NotFoundException(f"Investor '{slug}' not found")

    snapshot = await investor_service.get_investor_snapshot(db, investor.id)
    history = await investor_service.get_portfolio_history(db, investor.id)

    detail = InvestorDetail.model_validate(
        investor_service.investor_to_summary(investor, snapshot)
    )
    if snapshot:
        detail.latest_filing_date = snapshot.report_date
        detail.sector_breakdown = snapshot.sector_breakdown or {}
        detail.top_holdings = snapshot.top_holdings or []
    detail.portfolio_history = [
        {"report_date": s.report_date, "total_value_usd": s.total_value_usd, "total_positions": s.total_positions}
        for s in history
    ]
    return detail


@router.get("/{slug}/holdings", response_model=PaginatedResponse[HoldingSummary])
async def get_investor_holdings(
    slug: str,
    report_date: date | None = None,
    change_type: str | None = None,
    sort: str = "-value_usd",
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    investor = await investor_service.get_investor_by_slug(db, slug)
    if not investor:
        raise NotFoundException(f"Investor '{slug}' not found")

    holdings, total = await holding_service.get_holdings_for_investor(
        db, investor.id, report_date=report_date, change_type=change_type, sort=sort, page=page, limit=limit
    )
    return build_paginated_response(
        [HoldingSummary.model_validate(h) for h in holdings], total, page, limit
    )


@router.get("/{slug}/holdings/history", response_model=list[HoldingHistoryPoint])
async def get_holding_history(
    slug: str,
    security_id: int = Query(...),
    periods: int = Query(8, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    investor = await investor_service.get_investor_by_slug(db, slug)
    if not investor:
        raise NotFoundException(f"Investor '{slug}' not found")

    history = await holding_service.get_holding_history(db, investor.id, security_id, periods)
    return [HoldingHistoryPoint.model_validate(h) for h in history]


@router.get("/{slug}/snapshot")
async def get_snapshot(slug: str, db: AsyncSession = Depends(get_db)):
    investor = await investor_service.get_investor_by_slug(db, slug)
    if not investor:
        raise NotFoundException(f"Investor '{slug}' not found")

    snapshot = await investor_service.get_investor_snapshot(db, investor.id)
    if not snapshot:
        return {"total_value": None, "positions_count": None, "top_holdings": [], "sector_breakdown": {}}

    return {
        "total_value": snapshot.total_value_usd,
        "positions_count": snapshot.total_positions,
        "top_holdings": snapshot.top_holdings,
        "sector_breakdown": snapshot.sector_breakdown,
    }
