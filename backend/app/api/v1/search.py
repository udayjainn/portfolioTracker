from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.investor import InvestorSummary
from app.schemas.security import SecuritySummary
from app.services import search_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(
    q: str = Query(..., min_length=1),
    type: str = "investor,security",
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    results = await search_service.search(db, q, search_type=type, limit=limit)
    return {
        "investors": [InvestorSummary.model_validate(i) for i in results["investors"]],
        "securities": [SecuritySummary.model_validate(s) for s in results["securities"]],
    }


@router.get("/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    suggestions = await search_service.autocomplete(db, q, limit=limit)
    return {"suggestions": suggestions}
