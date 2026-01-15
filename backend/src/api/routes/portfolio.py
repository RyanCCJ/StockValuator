"""Portfolio API routes."""

from fastapi import APIRouter

from src.api.deps import CurrentUser, DbSession
from src.services.portfolio import get_portfolio_summary

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/summary")
async def get_summary(current_user: CurrentUser, db: DbSession):
    """Get portfolio summary with holdings, P&L, and total value."""
    summary = await get_portfolio_summary(db, current_user.id, current_user.base_currency)
    return summary
