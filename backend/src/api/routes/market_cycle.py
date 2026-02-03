"""Market Cycle API routes."""

from datetime import date, timedelta

import yfinance as yf
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.models.market_cycle import MarketCycleSnapshot
from src.schemas.market_cycle import (
    MarketCycleStatusResponse,
    MarketPulseItem,
    IndicatorStatus,
    MarketPulseHistoricalResponse,
    IndexHistoricalSeries,
    IndexHistoricalDataPoint,
    HistoricalTrendsResponse,
    HistoricalTrendData,
    OHLCDataPoint,
    LineDataPoint,
)
from src.services.market_cycle_service import MarketCycleService

router = APIRouter(prefix="/market-cycle", tags=["market-cycle"])


def _get_trend_status(price: float | None, ma200: float | None) -> str:
    """Determine trend status."""
    if price is None or ma200 is None:
        return "Unknown"
    return "Bullish" if price > ma200 else "Bearish"


def _get_pe_status(pe: float | None) -> str:
    """Determine PE status."""
    if pe is None:
        return "Unknown"
    if pe > 30:
        return "Overvalued"
    if pe < 15:
        return "Undervalued"
    return "Fair"


def _get_yield_status(spread: float | None) -> str:
    """Determine yield curve status."""
    if spread is None:
        return "Unknown"
    if spread < 0:
        return "Inverted"
    if spread < 0.5:
        return "Flat"
    return "Normal"


def _get_vix_status(vix: float | None) -> str:
    """Determine VIX status."""
    if vix is None:
        return "Unknown"
    if vix > 30:
        return "High Fear"
    if vix < 15:
        return "Complacent"
    return "Normal"


def _get_breadth_status(ma5: float | None, ma20: float | None) -> str:
    """Determine breadth status."""
    if ma5 is None or ma20 is None:
        return "Unknown"
    return "Improving" if ma5 > ma20 else "Weakening"


@router.get("/status", response_model=MarketCycleStatusResponse)
async def get_market_cycle_status(
    db: AsyncSession = Depends(get_db),
):
    """
    Get current market cycle status.

    Returns the current market phase, risk level, composite score,
    and detailed indicator values. Data is refreshed once per day
    on first request.
    """
    service = MarketCycleService()
    snapshot = await service.get_current_cycle(db)

    # Build market pulse items
    market_pulse = [
        MarketPulseItem(
            symbol="^DJI",
            name="Dow Jones",
            price=snapshot.djia_price,
            change_percent=snapshot.djia_change_percent,
        ),
        MarketPulseItem(
            symbol="^IXIC",
            name="Nasdaq",
            price=snapshot.nasdaq_price,
            change_percent=snapshot.nasdaq_change_percent,
        ),
        MarketPulseItem(
            symbol="^GSPC",
            name="S&P 500",
            price=snapshot.sp500_price,
            change_percent=snapshot.sp500_change_percent,
        ),
        MarketPulseItem(
            symbol="^RUT",
            name="Russell 2000",
            price=snapshot.russell_price,
            change_percent=snapshot.russell_change_percent,
        ),
    ]

    # Build indicator statuses
    indicators = [
        IndicatorStatus(
            name="Trend",
            value=snapshot.sp500_price,
            secondary_value=snapshot.sp500_ma200,
            status=_get_trend_status(snapshot.sp500_price, snapshot.sp500_ma200),
            description="S&P 500 Price / MA200",
        ),
        IndicatorStatus(
            name="Valuation",
            value=snapshot.shiller_pe,
            status=_get_pe_status(snapshot.shiller_pe),
            description="Shiller PE Ratio (CAPE)",
        ),
        IndicatorStatus(
            name="Recession",
            value=snapshot.yield_spread,
            status=_get_yield_status(snapshot.yield_spread),
            description="10Y-3M Treasury Spread",
        ),
        IndicatorStatus(
            name="Fear",
            value=snapshot.vix,
            status=_get_vix_status(snapshot.vix),
            description="VIX Index",
        ),
        IndicatorStatus(
            name="Breadth",
            value=snapshot.breadth_ma5,
            secondary_value=snapshot.breadth_ma20,
            status=_get_breadth_status(snapshot.breadth_ma5, snapshot.breadth_ma20),
            description="NYSE AD MA5 / MA20",
        ),
    ]

    return MarketCycleStatusResponse(
        snapshot_date=snapshot.snapshot_date,
        last_updated=snapshot.created_at,
        phase=snapshot.phase or "Unknown",
        phase_number=snapshot.phase_number or 0,
        risk_level=snapshot.risk_level or "Unknown",
        total_score=snapshot.total_score or 50,
        market_pulse=market_pulse,
        indicators=indicators,
        sp500_price=snapshot.sp500_price,
        sp500_ma200=snapshot.sp500_ma200,
        shiller_pe=snapshot.shiller_pe,
        yield_spread=snapshot.yield_spread,
        vix=snapshot.vix,
    )


@router.get("/pulse-history", response_model=MarketPulseHistoricalResponse)
async def get_market_pulse_history(
    period: str = Query("1y", description="Time period: 1y, 6mo, 3mo, 1mo"),
):
    """
    Get historical data for Market Pulse indices.

    Returns daily close prices for major indices over the specified period.
    Used for the Market Pulse performance comparison chart.
    """
    indices = [
        ("^DJI", "Dow Jones"),
        ("^IXIC", "Nasdaq"),
        ("^GSPC", "S&P 500"),
        ("^RUT", "Russell 2000"),
    ]

    result_indices: list[IndexHistoricalSeries] = []

    for symbol, name in indices:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)

            if hist.empty:
                result_indices.append(
                    IndexHistoricalSeries(symbol=symbol, name=name, data=[])
                )
                continue

            data_points = [
                IndexHistoricalDataPoint(
                    date=idx.strftime("%Y-%m-%d"),
                    close=float(row["Close"]),
                )
                for idx, row in hist.iterrows()
            ]

            result_indices.append(
                IndexHistoricalSeries(symbol=symbol, name=name, data=data_points)
            )
        except Exception:
            result_indices.append(
                IndexHistoricalSeries(symbol=symbol, name=name, data=[])
            )

    return MarketPulseHistoricalResponse(indices=result_indices)


@router.get("/trends-history", response_model=HistoricalTrendsResponse)
async def get_historical_trends(
    period: str = Query("1y", description="Time period: 2y, 1y, 6mo, 3mo"),
):
    """
    Get historical data for Historical Trends charts.

    Returns:
    - S&P 500: OHLC candlestick data (1 year)
    - VIX: OHLC candlestick data (1 year)
    """
    trends: list[HistoricalTrendData] = []

    # Fetch OHLC data for S&P 500
    try:
        sp500_ticker = yf.Ticker("^GSPC")
        sp500_hist = sp500_ticker.history(period=period)

        if not sp500_hist.empty:
            ohlc_data = [
                OHLCDataPoint(
                    time=idx.strftime("%Y-%m-%d"),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                )
                for idx, row in sp500_hist.iterrows()
            ]
            trends.append(
                HistoricalTrendData(
                    indicator="sp500",
                    chart_type="candlestick",
                    ohlc_data=ohlc_data,
                )
            )
    except Exception:
        trends.append(
            HistoricalTrendData(indicator="sp500", chart_type="candlestick", ohlc_data=[])
        )

    # Fetch OHLC data for VIX
    try:
        vix_ticker = yf.Ticker("^VIX")
        vix_hist = vix_ticker.history(period=period)

        if not vix_hist.empty:
            ohlc_data = [
                OHLCDataPoint(
                    time=idx.strftime("%Y-%m-%d"),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                )
                for idx, row in vix_hist.iterrows()
            ]
            trends.append(
                HistoricalTrendData(
                    indicator="vix",
                    chart_type="candlestick",
                    ohlc_data=ohlc_data,
                )
            )
    except Exception:
        trends.append(
            HistoricalTrendData(indicator="vix", chart_type="candlestick", ohlc_data=[])
        )

    return HistoricalTrendsResponse(trends=trends)
