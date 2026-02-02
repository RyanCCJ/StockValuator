"""Unit tests for MarketCycleService."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date

from src.services.market_cycle_service import MarketCycleService


class TestMarketCycleService:
    """Test suite for MarketCycleService."""

    @pytest.fixture
    def service(self):
        """Create a service instance."""
        return MarketCycleService()

    def test_calculate_bubble_top(self, service):
        """Test bubble top scenario (2000 dot-com peak)."""
        result = service.calculate_phase_and_score(
            sp500_price=100,
            sp500_ma200=90,  # Bull: price > MA200
            shiller_pe=40,   # Very high PE
            yield_spread=-0.5,  # Inverted
            vix=10,          # Low VIX (complacency)
            breadth_ma5=90,
            breadth_ma20=100,  # Weak: MA5 < MA20
        )

        # Expected: 50 + 15(PE) + 15(Yield) + 6(VIX) + 10(AD) = 96
        assert result["total_score"] == 96
        assert result["phase"] == "Distribution"
        assert result["phase_number"] == 3
        assert result["risk_level"] == "High"

    def test_calculate_crash_bottom(self, service):
        """Test crash bottom scenario (2008 financial crisis)."""
        result = service.calculate_phase_and_score(
            sp500_price=80,
            sp500_ma200=100,  # Bear: price < MA200
            shiller_pe=14,    # Low PE (cheap)
            yield_spread=0.2,  # Normal
            vix=50,           # High VIX (panic)
            breadth_ma5=100,
            breadth_ma20=90,  # Strong: MA5 > MA20
        )

        # Expected: 50 - 15(PE) - 25(VIX) - 10(AD) = 0
        assert result["total_score"] == 0
        assert result["phase"] == "Accumulation"
        assert result["phase_number"] == 1
        assert result["risk_level"] == "Low"

    def test_calculate_bull_market_low_risk(self, service):
        """Test normal bull market with low risk."""
        result = service.calculate_phase_and_score(
            sp500_price=5000,
            sp500_ma200=4800,  # Bull
            shiller_pe=22,     # Normal PE
            yield_spread=1.5,  # Positive spread
            vix=18,            # Normal VIX
            breadth_ma5=100,
            breadth_ma20=90,   # Strong: MA5 > MA20
        )

        # Low risk factors, should be around 50
        assert 50 <= result["total_score"] <= 60
        assert result["phase"] == "Mark-Up"
        assert result["phase_number"] == 2

    def test_calculate_bear_market_early(self, service):
        """Test early bear market (mark-down phase)."""
        result = service.calculate_phase_and_score(
            sp500_price=4500,
            sp500_ma200=4800,  # Bear: price < MA200
            shiller_pe=28,     # Still high PE
            yield_spread=-0.2, # Inverted (but not counted in bear)
            vix=22,            # Moderate VIX
            breadth_ma5=80,
            breadth_ma20=100,  # Weak: MA5 < MA20
        )

        # Low bottom factors, should be near 50
        assert result["phase"] == "Mark-Down"
        assert result["phase_number"] == 4
        assert result["risk_level"] == "High"

    def test_calculate_score_bounds(self, service):
        """Test that score is always bounded between 0-100."""
        # Extreme bullish scenario
        result_bull = service.calculate_phase_and_score(
            sp500_price=5000,
            sp500_ma200=4000,
            shiller_pe=50,     # Extreme PE
            yield_spread=-2.0, # Deep inversion
            vix=5,             # Extreme low VIX
            breadth_ma5=50,
            breadth_ma20=100,
        )
        assert 0 <= result_bull["total_score"] <= 100

        # Extreme bearish scenario
        result_bear = service.calculate_phase_and_score(
            sp500_price=4000,
            sp500_ma200=5000,
            shiller_pe=8,      # Very cheap
            vix=80,            # Extreme panic
            yield_spread=2.0,
            breadth_ma5=200,
            breadth_ma20=100,
        )
        assert 0 <= result_bear["total_score"] <= 100

    def test_calculate_with_none_values(self, service):
        """Test calculation handles None values gracefully."""
        result = service.calculate_phase_and_score(
            sp500_price=None,
            sp500_ma200=None,
            shiller_pe=None,
            yield_spread=None,
            vix=None,
            breadth_ma5=None,
            breadth_ma20=None,
        )

        # Should use defaults and return a valid result
        assert result["phase"] in ["Mark-Up", "Distribution"]
        assert result["total_score"] == 50  # Base score with no adjustments

    @pytest.mark.asyncio
    async def test_get_current_cycle_returns_existing_snapshot(self, service):
        """Test that existing snapshot is returned if available."""
        mock_snapshot = MagicMock()
        mock_snapshot.snapshot_date = date.today()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_snapshot
        mock_db.execute.return_value = mock_result

        result = await service.get_current_cycle(mock_db)

        assert result == mock_snapshot

    @pytest.mark.asyncio
    async def test_get_current_cycle_triggers_refresh_when_no_snapshot(self, service):
        """Test that refresh is triggered when no snapshot exists."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch.object(service, "refresh_data") as mock_refresh:
            mock_new_snapshot = MagicMock()
            mock_refresh.return_value = mock_new_snapshot

            result = await service.get_current_cycle(mock_db)

            mock_refresh.assert_called_once_with(mock_db)
            assert result == mock_new_snapshot
