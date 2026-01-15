"""Cash transaction schemas for API validation."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.cash import CashTransactionType


class CashTransactionBase(BaseModel):
    """Base cash transaction schema."""

    date: datetime
    type: CashTransactionType
    amount: Decimal = Field(..., gt=0, description="Transaction amount (positive)")
    currency: str = Field(default="USD", max_length=3)
    notes: str | None = Field(None, max_length=500)


class CashTransactionCreate(CashTransactionBase):
    """Schema for creating a cash transaction."""

    pass


class CashTransactionUpdate(BaseModel):
    """Schema for updating a cash transaction."""

    date: datetime | None = None
    type: CashTransactionType | None = None
    amount: Decimal | None = Field(None, gt=0)
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
