"""Trade schemas for API validation."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.trade import TradeType


class TradeBase(BaseModel):
    """Base trade schema with common fields."""

    symbol: str = Field(..., min_length=1, max_length=20)
    date: datetime
    type: TradeType
    price: Decimal = Field(..., gt=0)
    quantity: Decimal = Field(..., gt=0)
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
    type: TradeType | None = None
    price: Decimal | None = Field(None, gt=0)
    quantity: Decimal | None = Field(None, gt=0)
    fees: Decimal | None = Field(None, ge=0)
    currency: str | None = Field(None, min_length=3, max_length=3)
    notes: str | None = Field(None, max_length=5000)


class TradeResponse(TradeBase):
    """Schema for trade response."""

    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class TradeListResponse(BaseModel):
    """Schema for list of trades response."""

    trades: list[TradeResponse]
    total: int
