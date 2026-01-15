"""Trade service for CRUD operations."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.trade import Trade
from src.schemas.trade import TradeCreate, TradeUpdate


async def get_trades_by_user(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Trade], int]:
    """Get all trades for a user with pagination."""
    # Get total count
    count_query = select(func.count()).select_from(Trade).where(Trade.user_id == user_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get trades
    query = (
        select(Trade)
        .where(Trade.user_id == user_id)
        .order_by(Trade.date.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    trades = list(result.scalars().all())

    return trades, total


async def get_trade_by_id(db: AsyncSession, trade_id: UUID, user_id: UUID) -> Trade | None:
    """Get a specific trade by ID, ensuring it belongs to the user."""
    query = select(Trade).where(Trade.id == trade_id, Trade.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_trade(db: AsyncSession, user_id: UUID, trade_data: TradeCreate) -> Trade:
    """Create a new trade for a user."""
    trade = Trade(
        user_id=user_id,
        symbol=trade_data.symbol.upper(),
        date=trade_data.date,
        type=trade_data.type,
        price=trade_data.price,
        quantity=trade_data.quantity,
        fees=trade_data.fees,
        currency=trade_data.currency,
        notes=trade_data.notes,
    )
    db.add(trade)
    await db.flush()
    await db.refresh(trade)
    return trade


async def update_trade(
    db: AsyncSession,
    trade: Trade,
    trade_data: TradeUpdate,
) -> Trade:
    """Update an existing trade."""
    update_data = trade_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "symbol" and value:
            value = value.upper()
        setattr(trade, field, value)

    await db.flush()
    await db.refresh(trade)
    return trade


async def delete_trade(db: AsyncSession, trade: Trade) -> None:
    """Delete a trade."""
    await db.delete(trade)
    await db.flush()
