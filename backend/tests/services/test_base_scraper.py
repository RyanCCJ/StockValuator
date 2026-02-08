"""Unit tests for base scraper with browser pool and distributed locking."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.services.scrapers.base import BaseScraper, FinancialMetrics, ScraperError


class ConcreteScraper(BaseScraper):
    """Concrete implementation of BaseScraper for testing."""

    SOURCE_NAME = "test"
    CACHE_TTL = 3600

    async def _fetch_and_parse(self, symbol: str) -> FinancialMetrics:
        return FinancialMetrics(
            symbol=symbol.upper(),
            source=self.SOURCE_NAME,
            fetched_at=datetime.now(timezone.utc),
            pe_ratio=15.0,
        )


class TestBaseScraper:
    """Test suite for BaseScraper base class."""

    @pytest.fixture
    def scraper(self):
        """Create a concrete scraper instance."""
        return ConcreteScraper()

    @pytest.mark.asyncio
    async def test_get_data_returns_cached_when_available(self, scraper):
        """Test that get_data returns cached data when available."""
        cached_data = {
            "symbol": "AAPL",
            "source": "test",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "pe_ratio": 20.0,
        }

        with patch("src.services.scrapers.base.cache_get") as mock_cache_get:
            mock_cache_get.return_value = cached_data

            result = await scraper.get_data("AAPL")

            assert result.symbol == "AAPL"
            assert result.pe_ratio == 20.0
            mock_cache_get.assert_called_once_with("scraper:test:AAPL")

    @pytest.mark.asyncio
    async def test_get_data_fetches_when_not_cached(self, scraper):
        """Test that get_data fetches fresh data when not cached."""
        with patch("src.services.scrapers.base.cache_get") as mock_cache_get, \
             patch("src.services.scrapers.base.cache_set") as mock_cache_set, \
             patch("src.services.scrapers.base.ScrapeLocker") as MockLocker:
            mock_cache_get.return_value = None

            # Mock the locker to always acquire
            mock_locker_instance = MagicMock()
            mock_locker_instance.__aenter__ = AsyncMock(return_value=True)
            mock_locker_instance.__aexit__ = AsyncMock(return_value=None)
            MockLocker.return_value = mock_locker_instance

            result = await scraper.get_data("AAPL")

            assert result.symbol == "AAPL"
            assert result.pe_ratio == 15.0  # From _fetch_and_parse
            mock_cache_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_data_uses_distributed_locking(self, scraper):
        """Test that get_data uses distributed locking."""
        with patch("src.services.scrapers.base.cache_get") as mock_cache_get, \
             patch("src.services.scrapers.base.cache_set") as mock_cache_set, \
             patch("src.services.scrapers.base.ScrapeLocker") as MockLocker:
            mock_cache_get.return_value = None

            mock_locker_instance = MagicMock()
            mock_locker_instance.__aenter__ = AsyncMock(return_value=True)
            mock_locker_instance.__aexit__ = AsyncMock(return_value=None)
            MockLocker.return_value = mock_locker_instance

            await scraper.get_data("AAPL")

            # Verify ScrapeLocker was used with correct key
            MockLocker.assert_called_once_with("test:AAPL")

    @pytest.mark.asyncio
    async def test_get_data_waits_when_lock_not_acquired(self, scraper):
        """Test that get_data waits and checks cache when lock not acquired."""
        cached_data = {
            "symbol": "AAPL",
            "source": "test",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "pe_ratio": 25.0,
        }

        call_count = 0

        async def mock_cache_get_side_effect(key):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return None  # First call: not cached
            return cached_data  # Subsequent calls: cached

        with patch("src.services.scrapers.base.cache_get") as mock_cache_get, \
             patch("src.services.scrapers.base.ScrapeLocker") as MockLocker, \
             patch("asyncio.sleep") as mock_sleep:
            mock_cache_get.side_effect = mock_cache_get_side_effect
            mock_sleep.return_value = None

            # Mock locker to NOT acquire (another request is scraping)
            mock_locker_instance = MagicMock()
            mock_locker_instance.__aenter__ = AsyncMock(return_value=False)
            mock_locker_instance.__aexit__ = AsyncMock(return_value=None)
            MockLocker.return_value = mock_locker_instance

            result = await scraper.get_data("AAPL")

            # Should return cached data from wait loop
            assert result.pe_ratio == 25.0

    @pytest.mark.asyncio
    async def test_get_data_force_refresh_bypasses_cache(self, scraper):
        """Test that force_refresh bypasses cache check."""
        with patch("src.services.scrapers.base.cache_get") as mock_cache_get, \
             patch("src.services.scrapers.base.cache_set") as mock_cache_set, \
             patch("src.services.scrapers.base.ScrapeLocker") as MockLocker:

            mock_locker_instance = MagicMock()
            mock_locker_instance.__aenter__ = AsyncMock(return_value=True)
            mock_locker_instance.__aexit__ = AsyncMock(return_value=None)
            MockLocker.return_value = mock_locker_instance

            result = await scraper.get_data("AAPL", force_refresh=True)

            # cache_get should not be called for initial check
            mock_cache_get.assert_not_called()
            assert result.pe_ratio == 15.0


class TestFinancialMetrics:
    """Test suite for FinancialMetrics dataclass."""

    def test_to_dict(self):
        """Test that to_dict serializes correctly."""
        now = datetime.now(timezone.utc)
        metrics = FinancialMetrics(
            symbol="AAPL",
            source="test",
            fetched_at=now,
            pe_ratio=15.0,
            sector="Technology",
        )

        result = metrics.to_dict()

        assert result["symbol"] == "AAPL"
        assert result["source"] == "test"
        assert result["fetched_at"] == now.isoformat()
        assert result["pe_ratio"] == 15.0
        assert result["sector"] == "Technology"

    def test_from_dict(self):
        """Test that from_dict deserializes correctly."""
        now = datetime.now(timezone.utc)
        data = {
            "symbol": "AAPL",
            "source": "test",
            "fetched_at": now.isoformat(),
            "pe_ratio": 15.0,
            "sector": "Technology",
        }

        metrics = FinancialMetrics.from_dict(data)

        assert metrics.symbol == "AAPL"
        assert metrics.source == "test"
        assert metrics.pe_ratio == 15.0
        assert metrics.sector == "Technology"


class TestSafeFloat:
    """Test suite for _safe_float helper."""

    @pytest.fixture
    def scraper(self):
        return ConcreteScraper()

    def test_safe_float_with_number(self, scraper):
        """Test _safe_float with numeric input."""
        assert scraper._safe_float(42) == 42.0
        assert scraper._safe_float(3.14) == 3.14

    def test_safe_float_with_string(self, scraper):
        """Test _safe_float with string input."""
        assert scraper._safe_float("42") == 42.0
        assert scraper._safe_float("3.14") == 3.14
        assert scraper._safe_float("1,234.56") == 1234.56
        assert scraper._safe_float("$100") == 100.0
        assert scraper._safe_float("50%") == 50.0

    def test_safe_float_with_invalid(self, scraper):
        """Test _safe_float with invalid input."""
        assert scraper._safe_float(None) is None
        assert scraper._safe_float("") is None
        assert scraper._safe_float("-") is None
        assert scraper._safe_float("N/A") is None
        assert scraper._safe_float("NA") is None
        assert scraper._safe_float("invalid") is None
