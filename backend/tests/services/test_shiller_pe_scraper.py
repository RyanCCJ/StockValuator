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
        with patch("src.services.scrapers.shiller_pe.cache_get") as mock_cache_get:
            mock_cache_get.return_value = 35.5

            result = await scraper.get_shiller_pe()

            assert result == 35.5
            mock_cache_get.assert_called_once_with("scraper:shiller_pe:current")

    @pytest.mark.asyncio
    async def test_get_shiller_pe_force_refresh(self, scraper):
        """Test that force_refresh bypasses cache."""
        with patch("src.services.scrapers.shiller_pe.cache_get") as mock_cache_get, \
             patch("src.services.scrapers.shiller_pe.cache_set") as mock_cache_set, \
             patch.object(scraper, "_fetch_and_parse", return_value=36.2) as mock_fetch:

            result = await scraper.get_shiller_pe(force_refresh=True)

            assert result == 36.2
            mock_cache_get.assert_not_called()
            mock_fetch.assert_called_once()
            mock_cache_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_scraper_handles_missing_value(self, scraper):
        """Test that scraper raises error when PE value not found."""
        # Create mock Playwright objects
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value=None)

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        mock_async_playwright = MagicMock()
        mock_async_playwright.__aenter__ = AsyncMock(return_value=mock_playwright)
        mock_async_playwright.__aexit__ = AsyncMock()

        with patch("src.services.scrapers.shiller_pe.async_playwright", return_value=mock_async_playwright):
            with pytest.raises(ScraperError) as exc_info:
                await scraper._do_fetch()

            assert "Could not find Shiller PE value" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_scraper_parses_valid_response(self, scraper):
        """Test that scraper correctly parses a valid PE value from page."""
        # Create mock Playwright objects with valid response
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value="34.25")

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        mock_async_playwright = MagicMock()
        mock_async_playwright.__aenter__ = AsyncMock(return_value=mock_playwright)
        mock_async_playwright.__aexit__ = AsyncMock()

        with patch("src.services.scrapers.shiller_pe.async_playwright", return_value=mock_async_playwright):
            result = await scraper._do_fetch()

            assert result == 34.25
