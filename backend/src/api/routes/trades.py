"""Trade API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from src.api.deps import CurrentUser, DbSession
from src.schemas.trade import TradeCreate, TradeListResponse, TradeResponse, TradeUpdate
from src.services.trade_service import (
    create_trade,
    delete_trade,
    get_trade_by_id,
    get_trades_by_user,
    update_trade,
)

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("", response_model=TradeListResponse)
async def list_trades(
    current_user: CurrentUser,
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List all trades for the current user."""
    trades, total = await get_trades_by_user(db, current_user.id, skip, limit)
    return TradeListResponse(
        trades=[TradeResponse.model_validate(t) for t in trades],
        total=total,
    )


@router.post("", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
async def create_new_trade(
    trade_data: TradeCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Create a new trade."""
    trade = await create_trade(db, current_user.id, trade_data)
    await db.commit()
    return TradeResponse.model_validate(trade)


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Get a specific trade by ID."""
    trade = await get_trade_by_id(db, trade_id, current_user.id)
    if not trade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")
    return TradeResponse.model_validate(trade)


@router.put("/{trade_id}", response_model=TradeResponse)
async def update_existing_trade(
    trade_id: UUID,
    trade_data: TradeUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Update an existing trade."""
    trade = await get_trade_by_id(db, trade_id, current_user.id)
    if not trade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")

    updated_trade = await update_trade(db, trade, trade_data)
    await db.commit()
    return TradeResponse.model_validate(updated_trade)


@router.delete("/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_trade(
    trade_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Delete a trade."""
    trade = await get_trade_by_id(db, trade_id, current_user.id)
    if not trade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")

    await delete_trade(db, trade)
    await db.commit()
