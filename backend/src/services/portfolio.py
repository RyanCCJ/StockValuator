"""Portfolio service for P&L and performance calculations."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.trade import Trade, TradeType
from src.services.market_data import get_stock_prices_batch
from src.services.cash_service import get_cash_balance


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

        if symbol not in holdings:
            holdings[symbol] = {
                "symbol": symbol,
                "quantity": 0,
                "total_cost": 0,
                "realized_pnl": 0,
            }

        if trade.type == TradeType.BUY:
            holdings[symbol]["quantity"] += qty
            holdings[symbol]["total_cost"] += (qty * price) + fees
        else:  # SELL
            if holdings[symbol]["quantity"] > 0:
                avg_cost = holdings[symbol]["total_cost"] / holdings[symbol]["quantity"]
                cost_of_sold = avg_cost * qty
                proceeds = (qty * price) - fees
                holdings[symbol]["realized_pnl"] += proceeds - cost_of_sold
                holdings[symbol]["quantity"] -= qty
                holdings[symbol]["total_cost"] -= cost_of_sold

    # Remove positions with zero quantity
    holdings = {k: v for k, v in holdings.items() if v["quantity"] > 0.0001}

    # Get current prices
    symbols = list(holdings.keys())
    prices = await get_stock_prices_batch(symbols) if symbols else {}

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
