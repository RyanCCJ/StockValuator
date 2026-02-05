"""Cash transaction schemas for API validation."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CashTransactionBase(BaseModel):
    """Base cash transaction schema."""

    date: datetime
    action: str = Field(..., min_length=1, max_length=100)  # e.g., "Deposit", "Qualified Dividend"
    amount: Decimal = Field(..., description="Transaction amount (positive = money in, negative = money out)")
    currency: str = Field(default="USD", max_length=3)
    notes: str | None = Field(None, max_length=500)


class CashTransactionCreate(CashTransactionBase):
    """Schema for creating a cash transaction."""

    pass


class CashTransactionUpdate(BaseModel):
    """Schema for updating a cash transaction."""

    date: datetime | None = None
    action: str | None = Field(None, min_length=1, max_length=100)
    amount: Decimal | None = None
    currency: str | None = Field(None, max_length=3)
    notes: str | None = Field(None, max_length=500)


class CashTransactionResponse(CashTransactionBase):
    """Schema for cash transaction response."""

    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class CashTransactionListResponse(BaseModel):
    """Schema for listing cash transactions with balance."""

    transactions: list[CashTransactionResponse]
    total: int
    balance: Decimal
