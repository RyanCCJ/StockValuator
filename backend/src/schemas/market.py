"""Market data schemas for technical analysis feature."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OHLCVData(BaseModel):
    """Single OHLCV data point."""

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class SMAIndicator(BaseModel):
    """Simple Moving Average indicator data."""

    ma5: list[float | None]
    ma20: list[float | None]
    ma60: list[float | None]


class MACDIndicator(BaseModel):
    """MACD indicator data."""

    line: list[float | None]
    signal: list[float | None]
    histogram: list[float | None]


class BollingerBandsIndicator(BaseModel):
    """Bollinger Bands indicator data."""

    upper: list[float | None]
    middle: list[float | None]
    lower: list[float | None]


class StochasticIndicator(BaseModel):
    """Stochastic (KDJ) indicator data."""

    k: list[float | None]
    d: list[float | None]
    j: list[float | None]


class TechnicalIndicators(BaseModel):
    """Collection of technical indicators."""

    sma: SMAIndicator
    rsi: list[float | None]
    macd: MACDIndicator
    bollinger: BollingerBandsIndicator
    stochastic: StochasticIndicator
    volume: list[int]


class TechnicalDataResponse(BaseModel):
    """Response schema for technical analysis data."""

    symbol: str
    ohlcv: list[OHLCVData]
    indicators: TechnicalIndicators


class InstitutionalHolder(BaseModel):
    """Institutional holder information (for stocks)."""

    holder: str
    percent: float | None = None


class TopHolding(BaseModel):
    """ETF top holding information."""

    symbol: str
    name: str
    percent: float


class SectorWeighting(BaseModel):
    """ETF sector weighting information."""

    sector: str
    weight: float


class FundamentalDataResponse(BaseModel):
    """Response schema for fundamental data. Supports both stocks/crypto and ETFs."""

    # Common fields
    symbol: str
    is_etf: bool = False
    long_name: str | None = None
    market_cap: int | None = None
    beta: float | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None
    trailing_pe: float | None = None
    dividend_yield: float | None = None
    last_updated: datetime
    
    # Stock/Crypto specific fields
    description: str | None = None
    coin_image_url: str | None = None
    sector: str | None = None
    industry: str | None = None
    forward_pe: float | None = None
    trailing_eps: float | None = None
    forward_eps: float | None = None
    payout_ratio: float | None = None
    profit_margins: float | None = None
    revenue_growth: float | None = None
    analyst_rating: str | None = None
    book_value: float | None = None
    institutional_holders: list[InstitutionalHolder] = Field(default_factory=list)
    
    # ETF specific fields
    beta_3_year: float | None = None
    expense_ratio: float | None = None
    top_holdings: list[TopHolding] = Field(default_factory=list)
    sector_weightings: list[SectorWeighting] = Field(default_factory=list)

