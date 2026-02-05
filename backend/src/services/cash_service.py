"""Cash transaction service for CRUD operations."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.cash import CashTransaction
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

    With the new action-based system, we simply sum all amounts:
    - Positive amounts = money in (deposits, dividends, interest, sell proceeds)
    - Negative amounts = money out (withdrawals, taxes, fees, buy costs)

    For trades, we calculate:
    - Buy: -(price * quantity + fees) [money out]
    - Sell: +(price * quantity - fees) [money in]
    - Neutral (Stock Split, etc.): 0 [no cash impact]
    """
    from src.models.trade import Trade

    # Sum all cash transaction amounts (positive = in, negative = out)
    cash_query = (
        select(func.coalesce(func.sum(CashTransaction.amount), 0))
        .where(CashTransaction.user_id == user_id)
    )
    cash_result = await db.execute(cash_query)
    total_cash = Decimal(str(cash_result.scalar() or 0))

    # For trades, we need to determine if it's a buy or sell based on action
    # Buy actions typically include: Buy, Reinvest Shares
    # Sell actions typically include: Sell
    # Neutral actions: Stock Split, Stock Merger, Spin-off (no cash impact)

    # Buy-like actions (money out): -(price * quantity + fees)
    buy_actions = ['buy', 'reinvest']
    buy_query = (
        select(func.coalesce(func.sum(Trade.price * Trade.quantity + Trade.fees), 0))
        .where(Trade.user_id == user_id)
        .where(func.lower(Trade.action).in_(buy_actions))
    )
    buy_result = await db.execute(buy_query)
    total_buy_costs = Decimal(str(buy_result.scalar() or 0))

    # Sell-like actions (money in): +(price * quantity - fees)
    sell_actions = ['sell']
    sell_query = (
        select(func.coalesce(func.sum(Trade.price * Trade.quantity - Trade.fees), 0))
        .where(Trade.user_id == user_id)
        .where(func.lower(Trade.action).in_(sell_actions))
    )
    sell_result = await db.execute(sell_query)
    total_sell_proceeds = Decimal(str(sell_result.scalar() or 0))

    # Balance = cash transactions + sell proceeds - buy costs
    return total_cash + total_sell_proceeds - total_buy_costs


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
    """Create a new cash transaction.

    Amount sign is determined by action type:
    - Positive (money in): Deposit, Dividend, Interest
    - Negative (money out): Withdraw, Tax, Fee
    """
    # Determine amount sign based on action
    amount = abs(data.amount)  # Start with absolute value
    action_lower = data.action.lower()

    # Negative actions (money out)
    if action_lower in ['withdraw', 'tax', 'fee']:
        amount = -amount
    # Positive actions (money in): deposit, dividend, interest - keep positive

    transaction = CashTransaction(
        user_id=user_id,
        date=data.date,
        action=data.action,
        amount=amount,
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
