"""Market data service with yfinance and Redis caching."""

import json
from decimal import Decimal

import yfinance as yf

from src.core.cache import cache_get, cache_set


async def get_stock_price(symbol: str) -> dict | None:
    """
    Get current stock price for a symbol.
    Uses Redis caching with 5-minute TTL.
    """
    cache_key = f"price:{symbol.upper()}"

    # Try cache first
    cached = await cache_get(cache_key)
    if cached:
        return json.loads(cached)

    # Fetch from yfinance
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info

        if not info or info.last_price is None:
            return None

        price_data = {
            "symbol": symbol.upper(),
            "price": float(info.last_price),
            "currency": getattr(info, "currency", "USD") or "USD",
            "previous_close": float(info.previous_close) if info.previous_close else None,
        }

        # Calculate change
        if price_data["previous_close"]:
            change = price_data["price"] - price_data["previous_close"]
            change_percent = (change / price_data["previous_close"]) * 100
            price_data["change"] = round(change, 2)
            price_data["change_percent"] = round(change_percent, 2)

        # Cache for 5 minutes
        await cache_set(cache_key, json.dumps(price_data), ttl=300)

        return price_data
    except Exception:
        return None


async def get_stock_prices_batch(symbols: list[str]) -> dict[str, dict | None]:
    """Get prices for multiple symbols."""
    results = {}
    for symbol in symbols:
        results[symbol.upper()] = await get_stock_price(symbol)
    return results


async def get_exchange_rate(from_currency: str, to_currency: str) -> Decimal | None:
    """
    Get exchange rate between two currencies.
    Uses Redis caching with 1-hour TTL.
    """
    if from_currency == to_currency:
        return Decimal("1")

    cache_key = f"fx:{from_currency.upper()}{to_currency.upper()}"

    # Try cache first
    cached = await cache_get(cache_key)
    if cached:
        return Decimal(cached)

    # Fetch from yfinance using currency pair
    try:
        pair = f"{from_currency.upper()}{to_currency.upper()}=X"
        ticker = yf.Ticker(pair)
        info = ticker.fast_info

        if not info or info.last_price is None:
            return None

        rate = Decimal(str(info.last_price))

        # Cache for 1 hour
        await cache_set(cache_key, str(rate), ttl=3600)

        return rate
    except Exception:
        return None
