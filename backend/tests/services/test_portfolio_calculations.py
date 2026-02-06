"""Tests for portfolio calculation logic."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.models.trade import Trade
from src.services.portfolio import get_portfolio_summary, resolve_sector


class TestResolveSector:
    """Tests for the resolve_sector function."""

    def test_etf_classification(self):
        """ETF quote_type should return 'ETF' regardless of sector."""
        assert resolve_sector("ETF", "Technology") == "ETF"
        assert resolve_sector("ETF", None) == "ETF"

    def test_crypto_classification(self):
        """CRYPTOCURRENCY quote_type should return 'Crypto'."""
        assert resolve_sector("CRYPTOCURRENCY", None) == "Crypto"
        assert resolve_sector("CRYPTOCURRENCY", "Financial Services") == "Crypto"

    def test_stock_with_sector(self):
        """Stocks with a sector should return that sector."""
        assert resolve_sector("EQUITY", "Technology") == "Technology"
        assert resolve_sector("EQUITY", "Healthcare") == "Healthcare"
        assert resolve_sector(None, "Consumer Cyclical") == "Consumer Cyclical"

    def test_fallback_to_other(self):
        """Missing sector and non-ETF/Crypto should return 'Other'."""
        assert resolve_sector("EQUITY", None) == "Other"
        assert resolve_sector(None, None) == "Other"
        assert resolve_sector("EQUITY", "") == "Other"


class TestPortfolioCalculations:
    """Tests for the get_portfolio_summary function and P&L logic."""

    @pytest.fixture
    def user_id(self):
        """Generate a test user ID."""
        return uuid4()

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_external_services(self):
        """Mock external services (stock prices, cash balance, and metadata)."""
        with patch("src.services.portfolio.get_stock_prices_batch") as mock_prices, \
             patch("src.services.portfolio.get_cash_balance") as mock_cash, \
             patch("src.services.portfolio.get_holdings_metadata") as mock_metadata, \
             patch("src.services.portfolio.fetch_and_cache_metadata") as mock_fetch:
            # Default behavior
            mock_prices.return_value = {}
            mock_cash.return_value = Decimal("0")
            mock_metadata.return_value = {}
            mock_fetch.return_value = None
            yield mock_prices, mock_cash, mock_metadata, mock_fetch

    def _create_trade(self, user_id, symbol, action, quantity, price, fees=0, date=None):
        """Helper to create a Trade object."""
        if date is None:
            date = datetime.now()
        return Trade(
            user_id=user_id,
            symbol=symbol,
            action=action,
            quantity=Decimal(str(quantity)),
            price=Decimal(str(price)),
            fees=Decimal(str(fees)),
            date=date,
            currency="USD"
        )

    def _setup_db_result(self, mock_db, trades):
        """Setup mock db to return the list of trades."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = trades
        mock_db.execute.return_value = mock_result

    @pytest.mark.asyncio
    async def test_basic_buy_sell(self, mock_db, user_id, mock_external_services):
        """
        Verify Realized P/L calculation for a basic Buy/Sell scenario.
        Buy 10 @ $100 -> Cost $1000
        Sell 5 @ $120 -> Proceeds $600

        Cost of Sold = 5 * $100 = $500
        Realized P/L = $600 - $500 = $100
        Remaining: 5 shares, Cost Basis $500
        """
        trades = [
            self._create_trade(user_id, "AAPL", "Buy", 10, 100),
            self._create_trade(user_id, "AAPL", "Sell", 5, 120)
        ]
        self._setup_db_result(mock_db, trades)

        # Mock current price to be same as sell price just for clean unrealized output (optional)
        mock_prices, _, _, _ = mock_external_services
        mock_prices.return_value = {"AAPL": {"price": 120, "change": 0, "change_percent": 0}}

        summary = await get_portfolio_summary(mock_db, user_id)

        # Verify Realized P/L
        assert summary["realized_pnl"] == 100.0

        # Verify remaining holdings
        holdings = summary["holdings"]
        assert len(holdings) == 1
        aapl_holding = holdings[0]

        assert aapl_holding["symbol"] == "AAPL"
        assert aapl_holding["quantity"] == 5.0
        assert aapl_holding["cost_basis"] == 500.0

    @pytest.mark.asyncio
    async def test_partial_keyword_match(self, mock_db, user_id, mock_external_services):
        """
        Verify that partial keyword matching works for Buy and Sell actions.
        - "Purchase of Stock" -> contains "purchase" -> Buy
        - "Sold to Close" -> contains "sold" -> Sell
        """
        trades = [
            self._create_trade(user_id, "GOOGL", "Purchase of Stock", 10, 100),
            self._create_trade(user_id, "GOOGL", "Sold to Close", 5, 120)
        ]
        self._setup_db_result(mock_db, trades)

        summary = await get_portfolio_summary(mock_db, user_id)

        # Should behave exactly like test_basic_buy_sell
        assert summary["realized_pnl"] == 100.0

        holdings = summary["holdings"]
        assert len(holdings) == 1
        googl_holding = holdings[0]
        assert googl_holding["symbol"] == "GOOGL"
        assert googl_holding["quantity"] == 5.0

    @pytest.mark.asyncio
    async def test_adjustment_logic(self, mock_db, user_id, mock_external_services):
        """
        Verify Adjustment ("Adj") inversion logic.

        "Reinvest" is normally a Buy.
        "Reinvestment Adj" contains "reinvest" (Buy) AND "adj".
        This should flip it to be treated as a Sell (reducing quantity/cost).

        Scenario:
        1. Buy 10 @ $100
        2. Reinvestment Adj 1 @ $100

        Result should be equivalent to Selling 1 share at cost (no realized P/L change if price matches avg cost,
        or rather the logic treats it as effective_sell).

        If treated as sell:
        - Reduces Quantity
        - Reduces Total Cost (proportional to avg cost)
        """
        trades = [
            self._create_trade(user_id, "MSFT", "Buy", 10, 100),
            # "Reinvestment Adj" -> Treated as Sell logic
            self._create_trade(user_id, "MSFT", "Reinvestment Adj", 1, 100)
        ]
        self._setup_db_result(mock_db, trades)

        summary = await get_portfolio_summary(mock_db, user_id)

        holdings = summary["holdings"]
        assert len(holdings) == 1
        msft_holding = holdings[0]

        # Quantity should be 10 - 1 = 9
        assert msft_holding["quantity"] == 9.0

        # Cost basis should be 1000 - (100 avg * 1 qty) = 900
        assert msft_holding["cost_basis"] == 900.0

        # Realized P/L:
        # Proceeds = 1 * 100 = 100
        # Cost of Sold = 1 * 100 (Avg Cost) = 100
        # P/L = 0
        assert summary["realized_pnl"] == 0.0

    @pytest.mark.asyncio
    async def test_neutral_actions(self, mock_db, user_id, mock_external_services):
        """
        Verify Neutral Actions like "Stock Split".
        These are actions that match neither BUY nor SELL keywords (or match both/neither in a way that falls through).
        Actually "Stock Split" doesn't match any keyword in BUY_ACTIONS or SELL_ACTIONS.

        Logic:
        - Increases Quantity
        - Total Cost remains unchanged

        Scenario:
        1. Buy 10 @ $100 (Cost $1000)
        2. Stock Split 10 (Adding 10 shares)

        Result: 20 Shares, Cost $1000. Avg Cost $50.
        """
        trades = [
            self._create_trade(user_id, "TSLA", "Buy", 10, 100),
            # Stock Split typically comes with 0 price in many imports, or we just care about Qty
            self._create_trade(user_id, "TSLA", "Stock Split", 10, 0)
        ]
        self._setup_db_result(mock_db, trades)

        summary = await get_portfolio_summary(mock_db, user_id)

        holdings = summary["holdings"]
        assert len(holdings) == 1
        tsla_holding = holdings[0]

        assert tsla_holding["quantity"] == 20.0
        assert tsla_holding["cost_basis"] == 1000.0
        assert tsla_holding["avg_cost"] == 50.0

    @pytest.mark.asyncio
    async def test_fees_impact_on_cost_and_pnl(self, mock_db, user_id, mock_external_services):
        """
        Verify how fees affect cost basis and realized P/L.

        Scenario:
        1. Buy 10 @ $100 + $5 Fee.
           Total Cost = (10 * 100) + 5 = 1005.
           Avg Cost = 100.5

        2. Sell 5 @ $120 + $5 Fee.
           Proceeds = (5 * 120) - 5 = 595.
           Cost of Sold = 5 * 100.5 = 502.5
           Realized P/L = 595 - 502.5 = 92.5
        """
        trades = [
            self._create_trade(user_id, "AMD", "Buy", 10, 100, fees=5),
            self._create_trade(user_id, "AMD", "Sell", 5, 120, fees=5)
        ]
        self._setup_db_result(mock_db, trades)

        summary = await get_portfolio_summary(mock_db, user_id)

        # Verify Realized P/L
        # Expected: 92.5
        assert summary["realized_pnl"] == 92.5

        # Verify remaining holdings
        holdings = summary["holdings"]
        amd_holding = holdings[0]

        assert amd_holding["quantity"] == 5.0

        # Remaining Cost Basis = Original Total Cost - Cost of Sold
        # 1005 - 502.5 = 502.5
        assert amd_holding["cost_basis"] == 502.5


class TestPortfolioSectorEnrichment:
    """Tests for sector enrichment in portfolio holdings."""

    @pytest.fixture
    def user_id(self):
        """Generate a test user ID."""
        return uuid4()

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_external_services(self):
        """Mock external services (stock prices, cash balance, and metadata)."""
        with patch("src.services.portfolio.get_stock_prices_batch") as mock_prices, \
             patch("src.services.portfolio.get_cash_balance") as mock_cash, \
             patch("src.services.portfolio.get_holdings_metadata") as mock_metadata, \
             patch("src.services.portfolio.fetch_and_cache_metadata") as mock_fetch:
            # Default behavior
            mock_prices.return_value = {}
            mock_cash.return_value = Decimal("0")
            mock_metadata.return_value = {}
            mock_fetch.return_value = None
            yield mock_prices, mock_cash, mock_metadata, mock_fetch

    def _create_trade(self, user_id, symbol, action, quantity, price, fees=0, date=None):
        """Helper to create a Trade object."""
        if date is None:
            date = datetime.now()
        return Trade(
            user_id=user_id,
            symbol=symbol,
            action=action,
            quantity=Decimal(str(quantity)),
            price=Decimal(str(price)),
            fees=Decimal(str(fees)),
            date=date,
            currency="USD"
        )

    def _setup_db_result(self, mock_db, trades):
        """Setup mock db to return the list of trades."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = trades
        mock_db.execute.return_value = mock_result

    @pytest.mark.asyncio
    async def test_holdings_include_sector_field(self, mock_db, user_id, mock_external_services):
        """Verify holdings include the sector field from metadata."""
        trades = [
            self._create_trade(user_id, "AAPL", "Buy", 10, 100),
        ]
        self._setup_db_result(mock_db, trades)

        mock_prices, _, mock_metadata, _ = mock_external_services
        mock_prices.return_value = {"AAPL": {"price": 150, "change": 0, "change_percent": 0}}
        mock_metadata.return_value = {
            "AAPL": {"sector": "Technology", "industry": "Consumer Electronics", "quote_type": "EQUITY"}
        }

        summary = await get_portfolio_summary(mock_db, user_id)

        holdings = summary["holdings"]
        assert len(holdings) == 1
        assert holdings[0]["sector"] == "Technology"

    @pytest.mark.asyncio
    async def test_etf_sector_classification(self, mock_db, user_id, mock_external_services):
        """Verify ETFs are classified as 'ETF' sector."""
        trades = [
            self._create_trade(user_id, "SPY", "Buy", 5, 400),
        ]
        self._setup_db_result(mock_db, trades)

        mock_prices, _, mock_metadata, _ = mock_external_services
        mock_prices.return_value = {"SPY": {"price": 450, "change": 0, "change_percent": 0}}
        mock_metadata.return_value = {
            "SPY": {"sector": None, "industry": None, "quote_type": "ETF"}
        }

        summary = await get_portfolio_summary(mock_db, user_id)

        holdings = summary["holdings"]
        assert len(holdings) == 1
        assert holdings[0]["sector"] == "ETF"

    @pytest.mark.asyncio
    async def test_crypto_sector_classification(self, mock_db, user_id, mock_external_services):
        """Verify Crypto assets are classified as 'Crypto' sector."""
        trades = [
            self._create_trade(user_id, "BTC-USD", "Buy", 1, 50000),
        ]
        self._setup_db_result(mock_db, trades)

        mock_prices, _, mock_metadata, _ = mock_external_services
        mock_prices.return_value = {"BTC-USD": {"price": 60000, "change": 0, "change_percent": 0}}
        mock_metadata.return_value = {
            "BTC-USD": {"sector": None, "industry": None, "quote_type": "CRYPTOCURRENCY"}
        }

        summary = await get_portfolio_summary(mock_db, user_id)

        holdings = summary["holdings"]
        assert len(holdings) == 1
        assert holdings[0]["sector"] == "Crypto"

    @pytest.mark.asyncio
    async def test_missing_metadata_falls_back_to_other(self, mock_db, user_id, mock_external_services):
        """Verify assets with no metadata are classified as 'Other'."""
        trades = [
            self._create_trade(user_id, "UNKNOWN", "Buy", 10, 50),
        ]
        self._setup_db_result(mock_db, trades)

        mock_prices, _, mock_metadata, mock_fetch = mock_external_services
        mock_prices.return_value = {"UNKNOWN": {"price": 55, "change": 0, "change_percent": 0}}
        mock_metadata.return_value = {}
        mock_fetch.return_value = None  # No metadata found

        summary = await get_portfolio_summary(mock_db, user_id)

        holdings = summary["holdings"]
        assert len(holdings) == 1
        assert holdings[0]["sector"] == "Other"

    @pytest.mark.asyncio
    async def test_lazy_fetch_metadata_for_missing_symbols(self, mock_db, user_id, mock_external_services):
        """Verify lazy-loading fetches metadata for symbols missing from DB."""
        trades = [
            self._create_trade(user_id, "NVDA", "Buy", 5, 200),
        ]
        self._setup_db_result(mock_db, trades)

        mock_prices, _, mock_metadata, mock_fetch = mock_external_services
        mock_prices.return_value = {"NVDA": {"price": 250, "change": 0, "change_percent": 0}}
        mock_metadata.return_value = {}  # Not in DB
        mock_fetch.return_value = {
            "sector": "Technology",
            "industry": "Semiconductors",
            "quote_type": "EQUITY"
        }

        summary = await get_portfolio_summary(mock_db, user_id)

        # Verify fetch was called
        mock_fetch.assert_called_once()

        holdings = summary["holdings"]
        assert len(holdings) == 1
        assert holdings[0]["sector"] == "Technology"
