"""Alert schemas for price alert feature."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateAlertRequest(BaseModel):
    """Request schema for creating a price alert."""

    symbol: str = Field(..., min_length=1, max_length=20, example="AAPL")
    target_price: float = Field(..., gt=0, example=150.50)


class PriceAlertResponse(BaseModel):
    """Response schema for a price alert."""

    id: UUID
    symbol: str
    target_price: float
    initial_price: float
    status: str
    created_at: datetime
    triggered_at: datetime | None = None


class AlertListResponse(BaseModel):
    """Response schema for list of alerts."""

    alerts: list[PriceAlertResponse]
    count: int
