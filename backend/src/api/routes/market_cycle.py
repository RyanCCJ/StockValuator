"""Market Cycle API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.schemas.market_cycle import (
    MarketCycleStatusResponse,
    MarketPulseItem,
    IndicatorStatus,
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
            status=_get_trend_status(snapshot.sp500_price, snapshot.sp500_ma200),
            description=f"S&P 500 vs 200-day MA ({snapshot.sp500_ma200:.0f})" if snapshot.sp500_ma200 else "S&P 500 trend",
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
            status=_get_breadth_status(snapshot.breadth_ma5, snapshot.breadth_ma20),
            description="Nasdaq Net Issues Trend",
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
