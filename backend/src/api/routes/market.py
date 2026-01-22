"""Market data API routes."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.services.market_data import get_stock_price, get_technical_data, get_fundamental_data
from src.schemas.market import TechnicalDataResponse, FundamentalDataResponse

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/price/{symbol}")
async def get_price(symbol: str):
    """Get current stock price for a symbol."""
    price_data = await get_stock_price(symbol)

    if not price_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not fetch price for {symbol.upper()}",
        )

    return price_data


@router.get("/technical/{symbol}", response_model=TechnicalDataResponse)
async def get_technical(
    symbol: str,
    period: Literal["1mo", "3mo", "6mo", "1y", "2y"] = Query(default="1y"),
):
    """
    Get technical analysis data for a symbol.
    
    Returns OHLCV data and calculated technical indicators:
    - SMA (20, 60, 120)
    - RSI (14)
    - MACD (12, 26, 9)
    - Bollinger Bands (20, 2)
    - Stochastic KD (9, 3)
    - Volume
    """
    technical_data = await get_technical_data(symbol, period)

    if not technical_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not fetch technical data for {symbol.upper()}",
        )

    return technical_data


@router.get("/fundamental/{symbol}", response_model=FundamentalDataResponse)
async def get_fundamental(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get fundamental data for a symbol.
    
    Returns PE ratio, dividend yield, market cap, and major shareholders.
    Data is cached in the database for 24 hours.
    """
    fundamental_data = await get_fundamental_data(symbol, db)

    if not fundamental_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not fetch fundamental data for {symbol.upper()}",
        )

    return fundamental_data
