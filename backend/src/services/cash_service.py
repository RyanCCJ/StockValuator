"""Cash transaction service for CRUD operations."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.cash import CashTransaction, CashTransactionType
from src.schemas.cash import CashTransactionCreate, CashTransactionUpdate


async def get_cash_transactions_by_user(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[CashTransaction], int]:
    """Get all cash transactions for a user with pagination."""
    # Get total count
    count_query = (
        select(func.count()).select_from(CashTransaction).where(CashTransaction.user_id == user_id)
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get transactions
    query = (
        select(CashTransaction)
        .where(CashTransaction.user_id == user_id)
        .order_by(CashTransaction.date.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    transactions = list(result.scalars().all())

    return transactions, total


async def get_cash_balance(db: AsyncSession, user_id: UUID) -> Decimal:
    """
    Calculate total cash balance for a user.
    
    Cash Balance = Deposits - Withdrawals - Buy Costs + Sell Proceeds
    
    Where:
    - Buy Costs = (price * quantity) + fees
    - Sell Proceeds = (price * quantity) - fees
    """
    from src.models.trade import Trade, TradeType
    
    # Sum deposits
    deposit_query = (
        select(func.coalesce(func.sum(CashTransaction.amount), 0))
        .where(CashTransaction.user_id == user_id)
        .where(CashTransaction.type == CashTransactionType.DEPOSIT)
    )
    deposit_result = await db.execute(deposit_query)
    total_deposits = Decimal(str(deposit_result.scalar() or 0))

    # Sum withdrawals
    withdraw_query = (
        select(func.coalesce(func.sum(CashTransaction.amount), 0))
        .where(CashTransaction.user_id == user_id)
        .where(CashTransaction.type == CashTransactionType.WITHDRAW)
    )
    withdraw_result = await db.execute(withdraw_query)
    total_withdrawals = Decimal(str(withdraw_result.scalar() or 0))

    # Sum buy costs: (price * quantity) + fees
    buy_query = (
        select(func.coalesce(func.sum(Trade.price * Trade.quantity + Trade.fees), 0))
        .where(Trade.user_id == user_id)
        .where(Trade.type == TradeType.BUY)
    )
    buy_result = await db.execute(buy_query)
    total_buy_costs = Decimal(str(buy_result.scalar() or 0))

    # Sum sell proceeds: (price * quantity) - fees
    sell_query = (
        select(func.coalesce(func.sum(Trade.price * Trade.quantity - Trade.fees), 0))
        .where(Trade.user_id == user_id)
        .where(Trade.type == TradeType.SELL)
    )
    sell_result = await db.execute(sell_query)
    total_sell_proceeds = Decimal(str(sell_result.scalar() or 0))

    return total_deposits - total_withdrawals - total_buy_costs + total_sell_proceeds


async def get_cash_transaction_by_id(
    db: AsyncSession, transaction_id: UUID, user_id: UUID
) -> CashTransaction | None:
    """Get a specific cash transaction by ID."""
    query = select(CashTransaction).where(
        CashTransaction.id == transaction_id, CashTransaction.user_id == user_id
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_cash_transaction(
    db: AsyncSession, user_id: UUID, data: CashTransactionCreate
) -> CashTransaction:
    """Create a new cash transaction."""
    transaction = CashTransaction(
        user_id=user_id,
        date=data.date,
        type=data.type,
        amount=data.amount,
        currency=data.currency,
        notes=data.notes,
    )
    db.add(transaction)
    await db.flush()
    await db.refresh(transaction)
    return transaction


async def update_cash_transaction(
    db: AsyncSession, transaction: CashTransaction, data: CashTransactionUpdate
) -> CashTransaction:
    """Update a cash transaction."""
    update_data = data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(transaction, field, value)
        
    await db.flush()
    await db.refresh(transaction)
    return transaction


async def delete_cash_transaction(db: AsyncSession, transaction: CashTransaction) -> None:
    """Delete a cash transaction."""
    await db.delete(transaction)
    await db.flush()
