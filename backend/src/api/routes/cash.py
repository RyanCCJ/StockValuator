"""Cash transaction API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.api.deps import CurrentUser, DbSession
from src.schemas.cash import (
    CashTransactionCreate,
    CashTransactionListResponse,
    CashTransactionResponse,
    CashTransactionUpdate,
)
from src.services.cash_service import (
    create_cash_transaction,
    delete_cash_transaction,
    update_cash_transaction,
    get_cash_balance,
    get_cash_transaction_by_id,
    get_cash_transactions_by_user,
)

router = APIRouter(prefix="/cash", tags=["cash"])


@router.get("", response_model=CashTransactionListResponse)
async def get_cash_transactions(
    current_user: CurrentUser,
    db: DbSession,
    skip: int = 0,
    limit: int = 100,
):
    """Get all cash transactions with current balance."""
    transactions, total = await get_cash_transactions_by_user(db, current_user.id, skip, limit)
    balance = await get_cash_balance(db, current_user.id)

    return CashTransactionListResponse(
        transactions=[CashTransactionResponse.model_validate(t) for t in transactions],
        total=total,
        balance=balance,
    )


@router.post("", response_model=CashTransactionResponse, status_code=status.HTTP_201_CREATED)
async def add_cash_transaction(
    data: CashTransactionCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Add a new cash deposit or withdrawal."""
    transaction = await create_cash_transaction(db, current_user.id, data)
    await db.commit()
    return CashTransactionResponse.model_validate(transaction)


@router.patch("/{transaction_id}", response_model=CashTransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    data: CashTransactionUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Update a cash transaction (e.g., add notes)."""
    transaction = await get_cash_transaction_by_id(db, transaction_id, current_user.id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )
    
    transaction = await update_cash_transaction(db, transaction, data)
    await db.commit()
    return CashTransactionResponse.model_validate(transaction)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_cash_transaction(
    transaction_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Delete a cash transaction."""
    transaction = await get_cash_transaction_by_id(db, transaction_id, current_user.id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    await delete_cash_transaction(db, transaction)
    await db.commit()
