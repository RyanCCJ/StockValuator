"""Trade schemas for API validation."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class TradeBase(BaseModel):
    """Base trade schema with common fields."""

    symbol: str = Field(..., min_length=1, max_length=20)
    date: datetime
    action: str = Field(..., min_length=1, max_length=100)  # e.g., "Buy", "Sell", "Stock Split"
    price: Decimal = Field(..., ge=0)  # Allow 0 for special cases
    quantity: Decimal = Field(..., gt=0)
    amount: Decimal | None = Field(default=None)  # Original amount with sign (from CSV)
    fees: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    notes: str | None = Field(default=None, max_length=5000)


class TradeCreate(TradeBase):
    """Schema for creating a new trade."""

    pass


class TradeUpdate(BaseModel):
    """Schema for updating an existing trade."""

    symbol: str | None = Field(None, min_length=1, max_length=20)
    date: datetime | None = None
    action: str | None = Field(None, min_length=1, max_length=100)
    price: Decimal | None = Field(None, ge=0)
    quantity: Decimal | None = Field(None, gt=0)
    amount: Decimal | None = None  # Original amount with sign
    fees: Decimal | None = Field(None, ge=0)
    currency: str | None = Field(None, min_length=3, max_length=3)
    notes: str | None = Field(None, max_length=5000)


class TradeResponse(BaseModel):
    """Schema for trade response."""

    id: UUID
    user_id: UUID
    symbol: str
    date: datetime
    action: str
    price: Decimal
    quantity: Decimal
    amount: Decimal | None  # Original amount with sign (None if not provided)
    fees: Decimal
    currency: str
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TradeListResponse(BaseModel):
    """Schema for list of trades response."""

    trades: list[TradeResponse]
    total: int
