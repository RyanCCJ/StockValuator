"""Unit tests for market data service with async wrapper."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio


class TestMarketDataAsync:
    """Test suite for market data async operations."""

    @pytest.mark.asyncio
    async def test_get_stock_price_uses_executor(self):
        """Test that get_stock_price uses the executor for yfinance calls."""
        from src.services.market_data import get_stock_price

        with patch("src.services.market_data.cache_get") as mock_cache_get, \
             patch("src.services.market_data.cache_set") as mock_cache_set, \
             patch("src.services.market_data.run_in_yf_executor") as mock_executor:
            mock_cache_get.return_value = None
            mock_executor.return_value = {
                "symbol": "AAPL",
                "price": 150.0,
                "currency": "USD",
                "previous_close": 149.0,
                "change": 1.0,
                "change_percent": 0.67,
            }

            result = await get_stock_price("AAPL")

            mock_executor.assert_called_once()
            assert result["symbol"] == "AAPL"
            assert result["price"] == 150.0

    @pytest.mark.asyncio
    async def test_get_stock_price_uses_cache(self):
        """Test that get_stock_price returns cached data when available."""
        from src.services.market_data import get_stock_price

        cached_data = '{"symbol": "AAPL", "price": 150.0}'

        with patch("src.services.market_data.cache_get") as mock_cache_get:
            mock_cache_get.return_value = cached_data

            result = await get_stock_price("AAPL")

            assert result == {"symbol": "AAPL", "price": 150.0}

    @pytest.mark.asyncio
    async def test_get_stock_prices_batch_concurrent(self):
        """Test that get_stock_prices_batch fetches concurrently."""
        from src.services.market_data import get_stock_prices_batch

        with patch("src.services.market_data.get_stock_price") as mock_get_price:
            mock_get_price.side_effect = [
                {"symbol": "AAPL", "price": 150.0},
                {"symbol": "GOOGL", "price": 2800.0},
                {"symbol": "MSFT", "price": 300.0},
            ]

            result = await get_stock_prices_batch(["AAPL", "GOOGL", "MSFT"])

            assert len(result) == 3
            assert "AAPL" in result
            assert "GOOGL" in result
            assert "MSFT" in result
            # Should be called 3 times (once per symbol)
            assert mock_get_price.call_count == 3

    @pytest.mark.asyncio
    async def test_get_exchange_rate_uses_executor(self):
        """Test that get_exchange_rate uses the executor."""
        from src.services.market_data import get_exchange_rate

        with patch("src.services.market_data.cache_get") as mock_cache_get, \
             patch("src.services.market_data.cache_set") as mock_cache_set, \
             patch("src.services.market_data.run_in_yf_executor") as mock_executor:
            mock_cache_get.return_value = None
            mock_executor.return_value = 1.25

            result = await get_exchange_rate("USD", "EUR")

            mock_executor.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_exchange_rate_same_currency(self):
        """Test that get_exchange_rate returns 1 for same currency."""
        from src.services.market_data import get_exchange_rate
        from decimal import Decimal

        result = await get_exchange_rate("USD", "USD")

        assert result == Decimal("1")

    @pytest.mark.asyncio
    async def test_get_technical_data_uses_executor(self):
        """Test that get_technical_data uses the executor."""
        from src.services.market_data import get_technical_data

        with patch("src.services.market_data.cache_get") as mock_cache_get, \
             patch("src.services.market_data.cache_set") as mock_cache_set, \
             patch("src.services.market_data.run_in_yf_executor") as mock_executor:
            mock_cache_get.return_value = None
            mock_executor.return_value = (
                [{"date": "2024-01-01", "close": 150.0}],
                {"rsi": 50.0},
            )

            result = await get_technical_data("AAPL")

            mock_executor.assert_called_once()
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_fundamental_data_uses_executor(self):
        """Test that get_fundamental_data uses the executor."""
        from src.services.market_data import get_fundamental_data

        with patch("src.services.market_data.cache_get") as mock_cache_get, \
             patch("src.services.market_data.cache_set") as mock_cache_set, \
             patch("src.services.market_data.run_in_yf_executor") as mock_executor:
            mock_cache_get.return_value = None
            mock_executor.return_value = {
                "symbol": "AAPL",
                "is_etf": False,
                "long_name": "Apple Inc.",
            }

            result = await get_fundamental_data("AAPL")

            mock_executor.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_sp500_yield_uses_executor(self):
        """Test that get_sp500_yield uses the executor."""
        from src.services.market_data import get_sp500_yield

        with patch("src.services.market_data.cache_get") as mock_cache_get, \
             patch("src.services.market_data.cache_set") as mock_cache_set, \
             patch("src.services.market_data.run_in_yf_executor") as mock_executor:
            mock_cache_get.return_value = None
            mock_executor.return_value = 0.015

            result = await get_sp500_yield()

            mock_executor.assert_called_once()
            assert result == 0.015
