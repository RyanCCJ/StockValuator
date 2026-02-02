"""Market Cycle Pydantic schemas for API responses."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class IndicatorStatus(BaseModel):
    """Status for a single indicator."""

    name: str
    value: float | None
    status: str  # e.g., "Bullish", "Bearish", "Neutral", "Inverted"
    description: str


class MarketPulseItem(BaseModel):
    """Market pulse data for a single index."""

    symbol: str
    name: str
    price: float | None
    change_percent: float | None


class MarketCycleStatusResponse(BaseModel):
    """Response schema for market cycle status endpoint."""

    snapshot_date: date
    last_updated: datetime

    # Phase Information
    phase: str
    phase_number: int
    risk_level: str
    total_score: int

    # Market Pulse
    market_pulse: list[MarketPulseItem] = Field(default_factory=list)

    # Indicator Details
    indicators: list[IndicatorStatus] = Field(default_factory=list)

    # Raw data for charts
    sp500_price: float | None = None
    sp500_ma200: float | None = None
    shiller_pe: float | None = None
    yield_spread: float | None = None
    vix: float | None = None

    class Config:
        from_attributes = True


class MarketCycleHistoryItem(BaseModel):
    """Single item in historical data response."""

    date: date
    total_score: int | None
    phase_number: int | None
    sp500_price: float | None
    shiller_pe: float | None
    yield_spread: float | None
    vix: float | None


class MarketCycleHistoryResponse(BaseModel):
    """Response schema for historical market cycle data."""

    items: list[MarketCycleHistoryItem] = Field(default_factory=list)
    total: int = 0
