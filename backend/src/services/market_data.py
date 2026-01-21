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


async def get_technical_data(symbol: str, period: str = "1y") -> dict | None:
    """
    Get historical OHLCV data with calculated technical indicators.
    Uses Redis caching with 4-hour TTL.
    
    Args:
        symbol: Stock ticker symbol
        period: Data period (1mo, 3mo, 6mo, 1y, 2y)
        
    Returns:
        Dictionary with OHLCV data and calculated indicators
    """
    from src.services.technical_analysis import calculate_all_indicators
    
    symbol = symbol.upper()
    cache_key = f"technical:{symbol}:{period}"
    
    # Try cache first
    cached = await cache_get(cache_key)
    if cached:
        return json.loads(cached)
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval="1d")
        
        if df.empty:
            return None
        
        # Reset index to get date as a column
        df = df.reset_index()
        
        # Build OHLCV list
        ohlcv = []
        for _, row in df.iterrows():
            ohlcv.append({
                "date": row["Date"].strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })
        
        # Calculate indicators
        indicators = calculate_all_indicators(df)
        
        result = {
            "symbol": symbol,
            "ohlcv": ohlcv,
            "indicators": indicators,
        }
        
        # Cache for 4 hours (14400 seconds)
        await cache_set(cache_key, json.dumps(result), ttl=14400)
        
        return result
    except Exception:
        return None


async def get_fundamental_data(symbol: str, db=None) -> dict | None:
    """
    Get fundamental data for a stock/crypto or ETF.
    Uses Redis caching with 24-hour TTL.
    
    Returns different fields based on asset type:
    - Stocks/Crypto: sector, industry, PE ratios, EPS, analyst rating, institutional holders
    - ETFs: description, top holdings, sector weightings
    
    Args:
        symbol: Stock/ETF ticker symbol
        db: Database session (optional, currently not used)
        
    Returns:
        Dictionary with fundamental data including is_etf flag
    """
    from datetime import datetime, timezone
    
    symbol = symbol.upper()
    cache_key = f"fundamental:{symbol}"
    
    # Try cache first
    cached = await cache_get(cache_key)
    if cached:
        return json.loads(cached)
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        if not info:
            return None
        
        # Determine if ETF by checking quoteType (more reliable than funds_data presence)
        is_etf = info.get("quoteType") == "ETF"
        funds_data = None
        if is_etf:
            try:
                if hasattr(ticker, "funds_data") and ticker.funds_data:
                    funds_data = ticker.funds_data
            except Exception:
                pass
        
        # Common fields for both types
        fundamental_data = {
            "symbol": symbol,
            "is_etf": is_etf,
            "long_name": info.get("longName"),
            "market_cap": info.get("marketCap"),
            "beta": info.get("beta"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "trailing_pe": info.get("trailingPE"),
            "dividend_yield": info.get("dividendYield"),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        
        if is_etf:
            # ETF-specific fields
            fundamental_data["beta_3_year"] = info.get("beta3Year")
            fundamental_data["expense_ratio"] = info.get("netExpenseRatio")
            
            # Description from funds_data
            try:
                if funds_data and hasattr(funds_data, "description"):
                    fundamental_data["description"] = funds_data.description
            except Exception:
                fundamental_data["description"] = None
            
            # Top Holdings
            top_holdings = []
            try:
                if funds_data and funds_data.top_holdings is not None and not funds_data.top_holdings.empty:
                    df = funds_data.top_holdings.reset_index()
                    for _, row in df.iterrows():
                        top_holdings.append({
                            "symbol": row.get("Symbol", row.name) if hasattr(row, "name") else str(row.iloc[0]),
                            "name": row.get("Name", ""),
                            "percent": float(row.get("Holding Percent", 0)) * 100
                        })
            except Exception:
                pass
            fundamental_data["top_holdings"] = top_holdings
            
            # Sector Weightings
            sector_weightings = []
            try:
                if funds_data and funds_data.sector_weightings:
                    sw = funds_data.sector_weightings
                    # yfinance returns a dict like {'technology': 0.35, 'healthcare': 0.10, ...}
                    if isinstance(sw, dict):
                        for sector, weight in sw.items():
                            sector_weightings.append({
                                "sector": sector.replace("_", " ").title(),
                                "weight": float(weight) * 100
                            })
                    # Handle if it's a list of dicts (older format)
                    elif isinstance(sw, list):
                        for sector_dict in sw:
                            for sector, weight in sector_dict.items():
                                sector_weightings.append({
                                    "sector": sector.replace("_", " ").title(),
                                    "weight": float(weight) * 100
                                })
            except Exception:
                pass
            fundamental_data["sector_weightings"] = sector_weightings
            
        else:
            # Stock/Crypto-specific fields
            fundamental_data["description"] = info.get("longBusinessSummary") or info.get("description")
            fundamental_data["coin_image_url"] = info.get("coinImageUrl")
            fundamental_data["sector"] = info.get("sector")
            fundamental_data["industry"] = info.get("industry")
            fundamental_data["forward_pe"] = info.get("forwardPE")
            fundamental_data["trailing_eps"] = info.get("trailingEps")
            fundamental_data["forward_eps"] = info.get("forwardEps")
            fundamental_data["payout_ratio"] = info.get("payoutRatio")
            fundamental_data["profit_margins"] = info.get("profitMargins")
            fundamental_data["revenue_growth"] = info.get("revenueGrowth")
            fundamental_data["analyst_rating"] = info.get("averageAnalystRating")
            fundamental_data["book_value"] = info.get("bookValue")
            
            # Institutional Holders
            institutional_holders = []
            try:
                inst_holders = ticker.institutional_holders
                if inst_holders is not None and not inst_holders.empty:
                    for _, row in inst_holders.head(10).iterrows():
                        holder_name = row.get("Holder", "Unknown")
                        pct_held = row.get("pctHeld")
                        if pct_held is not None:
                            pct_held = float(pct_held) * 100
                        institutional_holders.append({
                            "holder": holder_name,
                            "percent": pct_held
                        })
            except Exception:
                pass
            fundamental_data["institutional_holders"] = institutional_holders
        
        # Cache for 24 hours (86400 seconds)
        await cache_set(cache_key, json.dumps(fundamental_data), ttl=86400)
        
        return fundamental_data
        
    except Exception:
        return None


