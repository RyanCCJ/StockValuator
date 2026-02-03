"""Market Cycle Pydantic schemas for API responses."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class IndicatorStatus(BaseModel):
    """Status for a single indicator."""

    name: str
    value: float | None
    secondary_value: float | None = None  # For indicators that need to show two values
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


class IndexHistoricalDataPoint(BaseModel):
    """Single data point for index historical data."""

    date: str  # ISO date string
    close: float


class IndexHistoricalSeries(BaseModel):
    """Historical series for a single index."""

    symbol: str
    name: str
    data: list[IndexHistoricalDataPoint] = Field(default_factory=list)


class MarketPulseHistoricalResponse(BaseModel):
    """Response schema for Market Pulse historical data (for performance chart)."""

    indices: list[IndexHistoricalSeries] = Field(default_factory=list)


class OHLCDataPoint(BaseModel):
    """OHLC data point for candlestick charts."""

    time: str  # ISO date string (lightweight-charts expects 'time' field)
    open: float
    high: float
    low: float
    close: float


class LineDataPoint(BaseModel):
    """Line data point for area/line charts."""

    time: str  # ISO date string
    value: float


class HistoricalTrendData(BaseModel):
    """Historical trend data for a single indicator."""

    indicator: str  # 'cape', 'yield', 'vix', 'sp500'
    chart_type: str  # 'candlestick' or 'line'
    ohlc_data: list[OHLCDataPoint] | None = None
    line_data: list[LineDataPoint] | None = None


class HistoricalTrendsResponse(BaseModel):
    """Response schema for Historical Trends data (for 2x2 grid charts)."""

    trends: list[HistoricalTrendData] = Field(default_factory=list)
