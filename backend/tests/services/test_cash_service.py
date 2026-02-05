"""Unit tests for cash_service.get_cash_balance function."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.models.cash import CashTransactionType
from src.models.trade import TradeType
from src.services.cash_service import get_cash_balance


class TestGetCashBalance:
    """Tests for the get_cash_balance function."""

    @pytest.fixture
    def user_id(self):
        """Generate a test user ID."""
        return uuid4()

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        return AsyncMock()

    def _create_mock_result(self, value):
        """Create a mock execute result that returns a scalar value."""
        result = MagicMock()
        result.scalar.return_value = value
        return result

    @pytest.mark.asyncio
    async def test_deposits_add_to_balance(self, mock_db, user_id):
        """Deposits should increase the cash balance."""
        # Mock the database responses in order:
        # deposit, withdraw, dividend, interest, tax, fee, buy, sell
        mock_db.execute.side_effect = [
            self._create_mock_result(Decimal("1000")),  # deposits
            self._create_mock_result(Decimal("0")),     # withdrawals
            self._create_mock_result(Decimal("0")),     # dividends
            self._create_mock_result(Decimal("0")),     # interest
            self._create_mock_result(Decimal("0")),     # taxes
            self._create_mock_result(Decimal("0")),     # fees
            self._create_mock_result(Decimal("0")),     # buys
            self._create_mock_result(Decimal("0")),     # sells
        ]

        balance = await get_cash_balance(mock_db, user_id)

        assert balance == Decimal("1000")

    @pytest.mark.asyncio
    async def test_withdrawals_subtract_from_balance(self, mock_db, user_id):
        """Withdrawals should decrease the cash balance."""
        mock_db.execute.side_effect = [
            self._create_mock_result(Decimal("1000")),  # deposits
            self._create_mock_result(Decimal("300")),   # withdrawals
            self._create_mock_result(Decimal("0")),     # dividends
            self._create_mock_result(Decimal("0")),     # interest
            self._create_mock_result(Decimal("0")),     # taxes
            self._create_mock_result(Decimal("0")),     # fees
            self._create_mock_result(Decimal("0")),     # buys
            self._create_mock_result(Decimal("0")),     # sells
        ]

        balance = await get_cash_balance(mock_db, user_id)

        assert balance == Decimal("700")  # 1000 - 300

    @pytest.mark.asyncio
    async def test_dividends_add_to_balance(self, mock_db, user_id):
        """Dividends should increase the cash balance."""
        mock_db.execute.side_effect = [
            self._create_mock_result(Decimal("0")),     # deposits
            self._create_mock_result(Decimal("0")),     # withdrawals
            self._create_mock_result(Decimal("150")),   # dividends
            self._create_mock_result(Decimal("0")),     # interest
            self._create_mock_result(Decimal("0")),     # taxes
            self._create_mock_result(Decimal("0")),     # fees
            self._create_mock_result(Decimal("0")),     # buys
            self._create_mock_result(Decimal("0")),     # sells
        ]

        balance = await get_cash_balance(mock_db, user_id)

        assert balance == Decimal("150")

    @pytest.mark.asyncio
    async def test_interest_adds_to_balance(self, mock_db, user_id):
        """Interest should increase the cash balance."""
        mock_db.execute.side_effect = [
            self._create_mock_result(Decimal("0")),     # deposits
            self._create_mock_result(Decimal("0")),     # withdrawals
            self._create_mock_result(Decimal("0")),     # dividends
            self._create_mock_result(Decimal("25.50")), # interest
            self._create_mock_result(Decimal("0")),     # taxes
            self._create_mock_result(Decimal("0")),     # fees
            self._create_mock_result(Decimal("0")),     # buys
            self._create_mock_result(Decimal("0")),     # sells
        ]

        balance = await get_cash_balance(mock_db, user_id)

        assert balance == Decimal("25.50")

    @pytest.mark.asyncio
    async def test_taxes_subtract_from_balance(self, mock_db, user_id):
        """Taxes should decrease the cash balance."""
        mock_db.execute.side_effect = [
            self._create_mock_result(Decimal("1000")),  # deposits
            self._create_mock_result(Decimal("0")),     # withdrawals
            self._create_mock_result(Decimal("0")),     # dividends
            self._create_mock_result(Decimal("0")),     # interest
            self._create_mock_result(Decimal("100")),   # taxes
            self._create_mock_result(Decimal("0")),     # fees
            self._create_mock_result(Decimal("0")),     # buys
            self._create_mock_result(Decimal("0")),     # sells
        ]

        balance = await get_cash_balance(mock_db, user_id)

        assert balance == Decimal("900")  # 1000 - 100

    @pytest.mark.asyncio
    async def test_fees_subtract_from_balance(self, mock_db, user_id):
        """Fees should decrease the cash balance."""
        mock_db.execute.side_effect = [
            self._create_mock_result(Decimal("1000")),  # deposits
            self._create_mock_result(Decimal("0")),     # withdrawals
            self._create_mock_result(Decimal("0")),     # dividends
            self._create_mock_result(Decimal("0")),     # interest
            self._create_mock_result(Decimal("0")),     # taxes
            self._create_mock_result(Decimal("15")),    # fees
            self._create_mock_result(Decimal("0")),     # buys
            self._create_mock_result(Decimal("0")),     # sells
        ]

        balance = await get_cash_balance(mock_db, user_id)

        assert balance == Decimal("985")  # 1000 - 15

    @pytest.mark.asyncio
    async def test_buy_trades_subtract_from_balance(self, mock_db, user_id):
        """Buy trades (cost + fees) should decrease the cash balance."""
        mock_db.execute.side_effect = [
            self._create_mock_result(Decimal("10000")), # deposits
            self._create_mock_result(Decimal("0")),     # withdrawals
            self._create_mock_result(Decimal("0")),     # dividends
            self._create_mock_result(Decimal("0")),     # interest
            self._create_mock_result(Decimal("0")),     # taxes
            self._create_mock_result(Decimal("0")),     # fees
            self._create_mock_result(Decimal("5000")),  # buys (price * quantity + fees)
            self._create_mock_result(Decimal("0")),     # sells
        ]

        balance = await get_cash_balance(mock_db, user_id)

        assert balance == Decimal("5000")  # 10000 - 5000

    @pytest.mark.asyncio
    async def test_sell_trades_add_to_balance(self, mock_db, user_id):
        """Sell trades (proceeds - fees) should increase the cash balance."""
        mock_db.execute.side_effect = [
            self._create_mock_result(Decimal("0")),     # deposits
            self._create_mock_result(Decimal("0")),     # withdrawals
            self._create_mock_result(Decimal("0")),     # dividends
            self._create_mock_result(Decimal("0")),     # interest
            self._create_mock_result(Decimal("0")),     # taxes
            self._create_mock_result(Decimal("0")),     # fees
            self._create_mock_result(Decimal("0")),     # buys
            self._create_mock_result(Decimal("7500")),  # sells (price * quantity - fees)
        ]

        balance = await get_cash_balance(mock_db, user_id)

        assert balance == Decimal("7500")

    @pytest.mark.asyncio
    async def test_complete_scenario_all_types(self, mock_db, user_id):
        """Test a complete scenario with all transaction types."""
        # Scenario:
        # + Deposits: $10,000
        # - Withdrawals: $1,000
        # + Dividends: $500
        # + Interest: $50
        # - Taxes: $75
        # - Fees: $25
        # - Buys: $4,000
        # + Sells: $2,000
        # Balance = 10000 - 1000 + 500 + 50 - 75 - 25 - 4000 + 2000 = 7450

        mock_db.execute.side_effect = [
            self._create_mock_result(Decimal("10000")),  # deposits
            self._create_mock_result(Decimal("1000")),   # withdrawals
            self._create_mock_result(Decimal("500")),    # dividends
            self._create_mock_result(Decimal("50")),     # interest
            self._create_mock_result(Decimal("75")),     # taxes
            self._create_mock_result(Decimal("25")),     # fees
            self._create_mock_result(Decimal("4000")),   # buys
            self._create_mock_result(Decimal("2000")),   # sells
        ]

        balance = await get_cash_balance(mock_db, user_id)

        assert balance == Decimal("7450")

    @pytest.mark.asyncio
    async def test_zero_balance_when_no_transactions(self, mock_db, user_id):
        """Should return zero when there are no transactions."""
        mock_db.execute.side_effect = [
            self._create_mock_result(Decimal("0")),  # deposits
            self._create_mock_result(Decimal("0")),  # withdrawals
            self._create_mock_result(Decimal("0")),  # dividends
            self._create_mock_result(Decimal("0")),  # interest
            self._create_mock_result(Decimal("0")),  # taxes
            self._create_mock_result(Decimal("0")),  # fees
            self._create_mock_result(Decimal("0")),  # buys
            self._create_mock_result(Decimal("0")),  # sells
        ]

        balance = await get_cash_balance(mock_db, user_id)

        assert balance == Decimal("0")

    @pytest.mark.asyncio
    async def test_negative_balance_possible(self, mock_db, user_id):
        """Balance can go negative if more is spent than deposited."""
        # Scenario: Buy more than deposited (margin account)
        mock_db.execute.side_effect = [
            self._create_mock_result(Decimal("1000")),   # deposits
            self._create_mock_result(Decimal("0")),      # withdrawals
            self._create_mock_result(Decimal("0")),      # dividends
            self._create_mock_result(Decimal("0")),      # interest
            self._create_mock_result(Decimal("0")),      # taxes
            self._create_mock_result(Decimal("0")),      # fees
            self._create_mock_result(Decimal("5000")),   # buys (more than deposits)
            self._create_mock_result(Decimal("0")),      # sells
        ]

        balance = await get_cash_balance(mock_db, user_id)

        assert balance == Decimal("-4000")

    @pytest.mark.asyncio
    async def test_handles_null_returns_as_zero(self, mock_db, user_id):
        """Should handle None returns from database as zero."""
        mock_db.execute.side_effect = [
            self._create_mock_result(None),  # deposits - None
            self._create_mock_result(None),  # withdrawals - None
            self._create_mock_result(None),  # dividends - None
            self._create_mock_result(None),  # interest - None
            self._create_mock_result(None),  # taxes - None
            self._create_mock_result(None),  # fees - None
            self._create_mock_result(None),  # buys - None
            self._create_mock_result(None),  # sells - None
        ]

        balance = await get_cash_balance(mock_db, user_id)

        assert balance == Decimal("0")

    @pytest.mark.asyncio
    async def test_decimal_precision_preserved(self, mock_db, user_id):
        """Should preserve decimal precision in calculations."""
        mock_db.execute.side_effect = [
            self._create_mock_result(Decimal("100.123456")),  # deposits
            self._create_mock_result(Decimal("0")),           # withdrawals
            self._create_mock_result(Decimal("10.654321")),   # dividends
            self._create_mock_result(Decimal("0.000001")),    # interest
            self._create_mock_result(Decimal("0")),           # taxes
            self._create_mock_result(Decimal("0")),           # fees
            self._create_mock_result(Decimal("0")),           # buys
            self._create_mock_result(Decimal("0")),           # sells
        ]

        balance = await get_cash_balance(mock_db, user_id)

        # 100.123456 + 10.654321 + 0.000001 = 110.777778
        assert balance == Decimal("110.777778")

    @pytest.mark.asyncio
    async def test_balance_formula_order(self, mock_db, user_id):
        """Test that the balance formula is applied correctly:
        Balance = deposits + dividends + interest + sell_proceeds
                  - withdrawals - taxes - fees - buy_costs
        """
        # Use specific values to verify the formula
        deposits = Decimal("100")
        withdrawals = Decimal("10")
        dividends = Decimal("20")
        interest = Decimal("5")
        taxes = Decimal("3")
        fees = Decimal("2")
        buys = Decimal("50")
        sells = Decimal("30")

        mock_db.execute.side_effect = [
            self._create_mock_result(deposits),
            self._create_mock_result(withdrawals),
            self._create_mock_result(dividends),
            self._create_mock_result(interest),
            self._create_mock_result(taxes),
            self._create_mock_result(fees),
            self._create_mock_result(buys),
            self._create_mock_result(sells),
        ]

        balance = await get_cash_balance(mock_db, user_id)

        expected = deposits + dividends + interest + sells - withdrawals - taxes - fees - buys
        # 100 + 20 + 5 + 30 - 10 - 3 - 2 - 50 = 90
        assert balance == expected
        assert balance == Decimal("90")
