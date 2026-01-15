"""Market data API routes."""

from fastapi import APIRouter, HTTPException, status

from src.services.market_data import get_stock_price

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
