"""Portfolio service for P&L and performance calculations."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.trade import Trade
from src.models.financial_data import FinancialData
from src.services.market_data import get_stock_prices_batch, get_fundamental_data
from src.services.cash_service import get_cash_balance

# Actions that are considered "buy" (money out, shares in)
BUY_ACTIONS = {'buy', 'reinvest', 'purchase', 'subscription'}
# Actions that are considered "sell" (money in, shares out)
SELL_ACTIONS = {'sell', 'sold', 'disposal', 'redemption'}


def resolve_sector(quote_type: str | None, sector: str | None) -> str:
    """
    Resolve the display sector for a holding based on the classification logic:
    1. If quoteType is "ETF" -> "ETF"
    2. If quoteType is "CRYPTOCURRENCY" -> "Crypto"
    3. If sector is available -> use that sector
    4. Fallback -> "Other"
    """
    if quote_type == "ETF":
        return "ETF"
    if quote_type == "CRYPTOCURRENCY":
        return "Crypto"
    if sector:
        return sector
    return "Other"


async def get_holdings_metadata(
    db: AsyncSession, symbols: list[str]
) -> dict[str, dict]:
    """
    Fetch sector and quote_type metadata for a list of symbols from FinancialData.
    Returns a dict mapping symbol -> {sector, quote_type, industry}.
    For symbols with multiple records, uses the most recently fetched one.
    """
    if not symbols:
        return {}

    # Get all records for the symbols, ordered by fetched_at descending
    query = (
        select(FinancialData)
        .where(FinancialData.symbol.in_(symbols))
        .order_by(FinancialData.fetched_at.desc())
    )
    result = await db.execute(query)
    records = result.scalars().all()

    # Build metadata dict - first occurrence per symbol is the most recent
    metadata = {}
    for record in records:
        if record.symbol not in metadata:
            metadata[record.symbol] = {
                "sector": record.sector,
                "industry": record.industry,
                "quote_type": record.quote_type,
            }
    return metadata


async def fetch_and_cache_metadata(
    db: AsyncSession, symbol: str
) -> dict | None:
    """
    Fetch metadata for a symbol from the external provider and cache it in FinancialData.
    Returns the metadata dict or None if not available.
    """
    fundamental_data = await get_fundamental_data(symbol)
    if not fundamental_data:
        return None

    # Check if record exists (get most recent by fetched_at)
    query = (
        select(FinancialData)
        .where(FinancialData.symbol == symbol)
        .order_by(FinancialData.fetched_at.desc())
        .limit(1)
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing record
        existing.sector = fundamental_data.get("sector")
        existing.industry = fundamental_data.get("industry")
        existing.quote_type = fundamental_data.get("quote_type")
    else:
        # Create new record with minimal data
        new_record = FinancialData(
            symbol=symbol,
            source="yfinance",
            sector=fundamental_data.get("sector"),
            industry=fundamental_data.get("industry"),
            quote_type=fundamental_data.get("quote_type"),
        )
        db.add(new_record)

    await db.commit()

    return {
        "sector": fundamental_data.get("sector"),
        "industry": fundamental_data.get("industry"),
        "quote_type": fundamental_data.get("quote_type"),
    }


async def get_portfolio_summary(db: AsyncSession, user_id: UUID, base_currency: str = "USD") -> dict:
    """
    Calculate portfolio summary including:
    - Holdings (positions with current value)
    - Total portfolio value
    - Total P&L (realized + unrealized)
    - Total cost basis
    """
    # Get all trades for the user
    query = select(Trade).where(Trade.user_id == user_id).order_by(Trade.date)
    result = await db.execute(query)
    trades = list(result.scalars().all())

    if not trades:
        return {
            "total_value": 0,
            "total_cost": 0,
            "total_pnl": 0,
            "total_pnl_percent": 0,
            "holdings": [],
            "realized_pnl": 0,
            "unrealized_pnl": 0,
        }

    # Calculate holdings using FIFO method
    holdings: dict[str, dict] = {}

    for trade in trades:
        symbol = trade.symbol
        qty = float(trade.quantity)
        price = float(trade.price)
        fees = float(trade.fees)
        action_lower = trade.action.lower()

        if symbol not in holdings:
            holdings[symbol] = {
                "symbol": symbol,
                "quantity": 0,
                "total_cost": 0,
                "realized_pnl": 0,
            }


        # Determine transaction type based on keywords and adjustment flag
        # We look for partial matches (substrings) instead of exact matches
        is_buy_signal = any(k in action_lower for k in BUY_ACTIONS)
        is_sell_signal = any(k in action_lower for k in SELL_ACTIONS)
        is_adj = "adj" in action_lower

        # Apply logic with adjustment inversion
        # If 'adj' is present, it inverts the logic (Buy -> Sell, Sell -> Buy)
        # e.g., "Reinvestment Adj" (Buy keyword + Adj) -> Treated as Sell (deducts cost/qty)
        effective_buy = (is_buy_signal and not is_adj) or (is_sell_signal and is_adj)
        effective_sell = (is_sell_signal and not is_adj) or (is_buy_signal and is_adj)

        if effective_buy:
            holdings[symbol]["quantity"] += qty
            holdings[symbol]["total_cost"] += (qty * price) + fees
        elif effective_sell:
            if holdings[symbol]["quantity"] > 0:
                avg_cost = holdings[symbol]["total_cost"] / holdings[symbol]["quantity"]
                cost_of_sold = avg_cost * qty
                proceeds = (qty * price) - fees
                holdings[symbol]["realized_pnl"] += proceeds - cost_of_sold
                holdings[symbol]["quantity"] -= qty
                holdings[symbol]["total_cost"] -= cost_of_sold
        # Neutral actions (Stock Split, Merger, etc.) - just adjust quantity, no cost change
        else:
            # For stock splits and similar, we add shares but don't change cost basis
            # The quantity change is already in the trade
            holdings[symbol]["quantity"] += qty

    # Remove positions with zero quantity
    holdings = {k: v for k, v in holdings.items() if v["quantity"] > 0.0001}

    # Get current prices
    symbols = list(holdings.keys())
    prices = await get_stock_prices_batch(symbols) if symbols else {}

    # Fetch metadata (sector, quote_type) for all holdings
    metadata = await get_holdings_metadata(db, symbols) if symbols else {}

    # Identify symbols missing metadata OR missing quote_type (needs refresh)
    symbols_needing_fetch = [
        s for s in symbols
        if s not in metadata or metadata[s].get("quote_type") is None
    ]
    for symbol in symbols_needing_fetch:
        fetched = await fetch_and_cache_metadata(db, symbol)
        if fetched:
            metadata[symbol] = fetched

    # Calculate current values and unrealized P&L
    result_holdings = []
    total_value = Decimal("0")
    total_cost = Decimal("0")
    total_realized_pnl = Decimal("0")
    total_unrealized_pnl = Decimal("0")

    for symbol, holding in holdings.items():
        price_data = prices.get(symbol)
        current_price = Decimal(str(price_data["price"])) if price_data else None

        qty = Decimal(str(holding["quantity"]))
        cost = Decimal(str(holding["total_cost"]))
        avg_cost = cost / qty if qty > 0 else Decimal("0")

        if current_price:
            current_value = qty * current_price
            unrealized = current_value - cost
        else:
            current_value = cost  # Fallback to cost if no price available
            unrealized = Decimal("0")

        total_value += current_value
        total_cost += cost
        total_realized_pnl += Decimal(str(holding["realized_pnl"]))
        total_unrealized_pnl += unrealized

        # Get sector from metadata
        symbol_metadata = metadata.get(symbol, {})
        sector = resolve_sector(
            symbol_metadata.get("quote_type"),
            symbol_metadata.get("sector")
        )

        result_holdings.append({
            "symbol": symbol,
            "quantity": float(qty),
            "avg_cost": float(avg_cost),
            "current_price": float(current_price) if current_price else None,
            "current_value": float(current_value),
            "cost_basis": float(cost),
            "unrealized_pnl": float(unrealized),
            "unrealized_pnl_percent": float((unrealized / cost) * 100) if cost > 0 else 0,
            "price_change": price_data.get("change") if price_data else None,
            "price_change_percent": price_data.get("change_percent") if price_data else None,
            "sector": sector,
        })

    # Sort by value descending
    result_holdings.sort(key=lambda x: x["current_value"], reverse=True)

    total_pnl = total_realized_pnl + total_unrealized_pnl
    pnl_percent = float((total_pnl / total_cost) * 100) if total_cost > 0 else 0

    # Get cash balance
    cash_balance = await get_cash_balance(db, user_id)
    cash_balance_float = float(cash_balance)

    # Calculate total portfolio (cash + investments)
    total_portfolio = float(total_value) + cash_balance_float

    # Cash ratio as percentage
    cash_ratio = (cash_balance_float / total_portfolio * 100) if total_portfolio > 0 else 0

    return {
        "total_value": float(total_value),
        "total_cost": float(total_cost),
        "total_pnl": float(total_pnl),
        "total_pnl_percent": round(pnl_percent, 2),
        "realized_pnl": float(total_realized_pnl),
        "unrealized_pnl": float(total_unrealized_pnl),
        "holdings": result_holdings,
        "holdings_count": len(result_holdings),
        "cash_balance": cash_balance_float,
        "total_portfolio": total_portfolio,
        "cash_ratio": round(cash_ratio, 2),
    }
