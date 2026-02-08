"""Unit tests for ShillerPEScraper."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.scrapers.shiller_pe import ShillerPEScraper
from src.services.scrapers.base import ScraperError


class TestShillerPEScraper:
    """Test suite for ShillerPEScraper."""

    @pytest.fixture
    def scraper(self):
        """Create a scraper instance."""
        return ShillerPEScraper()

    @pytest.mark.asyncio
    async def test_parse_valid_pe_value(self, scraper):
        """Test parsing a valid PE value."""
        # Test the _safe_float helper
        assert scraper._safe_float("32.45") == 32.45
        assert scraper._safe_float("32") == 32.0
        assert scraper._safe_float("32.45%") == 32.45

    @pytest.mark.asyncio
    async def test_parse_invalid_pe_value(self, scraper):
        """Test parsing invalid PE values."""
        assert scraper._safe_float(None) is None
        assert scraper._safe_float("") is None
        assert scraper._safe_float("-") is None
        assert scraper._safe_float("N/A") is None

    @pytest.mark.asyncio
    async def test_get_shiller_pe_with_cache_hit(self, scraper):
        """Test that cached value is returned when available."""
        with patch("src.core.cache.cache_get") as mock_cache_get:
            mock_cache_get.return_value = 35.5

            result = await scraper.get_shiller_pe()

            assert result == 35.5
            mock_cache_get.assert_called_once_with("scraper:shiller_pe:current")

    @pytest.mark.asyncio
    async def test_get_shiller_pe_force_refresh(self, scraper):
        """Test that force_refresh bypasses cache."""
        with patch("src.core.cache.cache_get") as mock_cache_get, \
             patch("src.core.cache.cache_set") as mock_cache_set, \
             patch.object(scraper, "_fetch_and_parse", return_value=36.2) as mock_fetch:

            result = await scraper.get_shiller_pe(force_refresh=True)

            assert result == 36.2
            mock_cache_get.assert_not_called()
            mock_fetch.assert_called_once()
            mock_cache_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_scraper_handles_missing_value(self, scraper):
        """Test that scraper raises error when PE value not found."""
        # Create mock page
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value=None)
        mock_page.close = AsyncMock()

        # Create mock context that returns the page
        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)

        # Create mock browser
        mock_browser = AsyncMock()

        # Mock the BrowserContextManager as an async context manager
        async def mock_aenter(self):
            return (mock_browser, mock_context)

        async def mock_aexit(self, exc_type, exc_val, exc_tb):
            return None

        with patch("src.services.scrapers.shiller_pe.BrowserContextManager") as MockBCM:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = mock_aenter
            mock_instance.__aexit__ = mock_aexit
            MockBCM.return_value = mock_instance

            with pytest.raises(ScraperError) as exc_info:
                await scraper._do_fetch()

            assert "Could not find Shiller PE value" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_scraper_parses_valid_response(self, scraper):
        """Test that scraper correctly parses a valid PE value from page."""
        # Create mock page with valid response
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value="34.25")
        mock_page.close = AsyncMock()

        # Create mock context that returns the page
        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)

        # Create mock browser
        mock_browser = AsyncMock()

        # Mock the BrowserContextManager as an async context manager
        async def mock_aenter(self):
            return (mock_browser, mock_context)

        async def mock_aexit(self, exc_type, exc_val, exc_tb):
            return None

        with patch("src.services.scrapers.shiller_pe.BrowserContextManager") as MockBCM:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = mock_aenter
            mock_instance.__aexit__ = mock_aexit
            MockBCM.return_value = mock_instance

            result = await scraper._do_fetch()

            assert result == 34.25

    @pytest.mark.asyncio
    async def test_extract_pe_value_valid(self, scraper):
        """Test _extract_pe_value with valid inputs."""
        assert scraper._extract_pe_value("Current\nShiller PE Ratio:\n40.46\nmore text") == 40.46
        assert scraper._extract_pe_value("35.5") == 35.5
        assert scraper._extract_pe_value("The PE is 28.3 today") == 28.3

    @pytest.mark.asyncio
    async def test_extract_pe_value_invalid(self, scraper):
        """Test _extract_pe_value with invalid inputs."""
        assert scraper._extract_pe_value(None) is None
        assert scraper._extract_pe_value("") is None
        assert scraper._extract_pe_value("No numbers here") is None
        assert scraper._extract_pe_value("3.5") is None  # Below 5
        assert scraper._extract_pe_value("100.0") is None  # Above 60
