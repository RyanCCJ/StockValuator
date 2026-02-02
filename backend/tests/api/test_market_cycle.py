"""Integration tests for Market Cycle API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date, datetime, timezone

from fastapi.testclient import TestClient


class TestMarketCycleAPI:
    """Test suite for Market Cycle API endpoints."""

    @pytest.fixture
    def mock_snapshot(self):
        """Create a mock snapshot."""
        snapshot = MagicMock()
        snapshot.snapshot_date = date.today()
        snapshot.created_at = datetime.now(timezone.utc)
        snapshot.phase = "Mark-Up"
        snapshot.phase_number = 2
        snapshot.risk_level = "Low"
        snapshot.total_score = 65
        snapshot.sp500_price = 5000.0
        snapshot.sp500_ma200 = 4800.0
        snapshot.sp500_change_percent = 0.5
        snapshot.shiller_pe = 28.5
        snapshot.treasury_10y = 4.2
        snapshot.treasury_3m = 5.1
        snapshot.yield_spread = -0.9
        snapshot.vix = 18.5
        snapshot.breadth_ma5 = 120.0
        snapshot.breadth_ma20 = 100.0
        snapshot.djia_price = 38500.0
        snapshot.djia_change_percent = 0.3
        snapshot.nasdaq_price = 16200.0
        snapshot.nasdaq_change_percent = 0.7
        snapshot.russell_price = 2050.0
        snapshot.russell_change_percent = 0.2
        return snapshot

    @pytest.mark.asyncio
    async def test_get_status_returns_snapshot(self, mock_snapshot):
        """Test that GET /market-cycle/status returns proper response."""
        from src.api.routes.market_cycle import get_market_cycle_status

        mock_db = AsyncMock()

        with patch("src.api.routes.market_cycle.MarketCycleService") as MockService:
            mock_service_instance = MagicMock()
            mock_service_instance.get_current_cycle = AsyncMock(return_value=mock_snapshot)
            MockService.return_value = mock_service_instance

            response = await get_market_cycle_status(db=mock_db)

            assert response.phase == "Mark-Up"
            assert response.phase_number == 2
            assert response.risk_level == "Low"
            assert response.total_score == 65
            assert len(response.market_pulse) == 4
            assert len(response.indicators) == 5

    @pytest.mark.asyncio
    async def test_get_status_indicator_statuses(self, mock_snapshot):
        """Test that indicators have correct status values."""
        from src.api.routes.market_cycle import get_market_cycle_status

        mock_db = AsyncMock()

        with patch("src.api.routes.market_cycle.MarketCycleService") as MockService:
            mock_service_instance = MagicMock()
            mock_service_instance.get_current_cycle = AsyncMock(return_value=mock_snapshot)
            MockService.return_value = mock_service_instance

            response = await get_market_cycle_status(db=mock_db)

            # Find each indicator
            trend = next(i for i in response.indicators if i.name == "Trend")
            valuation = next(i for i in response.indicators if i.name == "Valuation")
            recession = next(i for i in response.indicators if i.name == "Recession")
            fear = next(i for i in response.indicators if i.name == "Fear")
            breadth = next(i for i in response.indicators if i.name == "Breadth")

            assert trend.status == "Bullish"  # price > ma200
            assert valuation.status == "Fair"  # PE between 15-30
            assert recession.status == "Inverted"  # yield_spread < 0
            assert fear.status == "Normal"  # VIX between 15-30
            assert breadth.status == "Improving"  # MA5 > MA20

    @pytest.mark.asyncio
    async def test_market_pulse_data(self, mock_snapshot):
        """Test that market pulse data is correctly formatted."""
        from src.api.routes.market_cycle import get_market_cycle_status

        mock_db = AsyncMock()

        with patch("src.api.routes.market_cycle.MarketCycleService") as MockService:
            mock_service_instance = MagicMock()
            mock_service_instance.get_current_cycle = AsyncMock(return_value=mock_snapshot)
            MockService.return_value = mock_service_instance

            response = await get_market_cycle_status(db=mock_db)

            # Check each index in market pulse
            symbols = [item.symbol for item in response.market_pulse]
            assert "^DJI" in symbols
            assert "^IXIC" in symbols
            assert "^GSPC" in symbols
            assert "^RUT" in symbols

            djia = next(i for i in response.market_pulse if i.symbol == "^DJI")
            assert djia.name == "Dow Jones"
            assert djia.price == 38500.0
            assert djia.change_percent == 0.3
