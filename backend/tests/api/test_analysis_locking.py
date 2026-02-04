"""Unit tests for analysis route with distributed locking."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestAnalysisPrefetch:
    """Test suite for analysis prefetch with distributed locking."""

    @pytest.mark.asyncio
    async def test_is_prefetching_checks_redis_lock(self):
        """Test that _is_prefetching checks Redis lock."""
        from src.api.routes.analysis import _is_prefetching

        with patch("src.core.cache.get_redis") as mock_get_redis:
            mock_client = AsyncMock()
            mock_client.exists.return_value = 1
            mock_get_redis.return_value = mock_client

            result = await _is_prefetching("AAPL")

            assert result is True
            mock_client.exists.assert_called_once_with("lock:prefetch:AAPL")

    @pytest.mark.asyncio
    async def test_is_prefetching_returns_false_when_no_lock(self):
        """Test that _is_prefetching returns False when no lock exists."""
        from src.api.routes.analysis import _is_prefetching

        with patch("src.core.cache.get_redis") as mock_get_redis:
            mock_client = AsyncMock()
            mock_client.exists.return_value = 0
            mock_get_redis.return_value = mock_client

            result = await _is_prefetching("AAPL")

            assert result is False

    @pytest.mark.asyncio
    async def test_background_prefetch_acquires_lock(self):
        """Test that background prefetch acquires distributed lock."""
        from src.api.routes.analysis import _background_prefetch

        with patch("src.api.routes.analysis.acquire_scrape_lock") as mock_acquire, \
             patch("src.api.routes.analysis.release_scrape_lock") as mock_release, \
             patch("src.api.routes.analysis.get_financial_data") as mock_get_data:
            mock_acquire.return_value = True
            mock_get_data.return_value = MagicMock()

            await _background_prefetch("AAPL", MagicMock())

            mock_acquire.assert_called_once_with("prefetch:AAPL", ttl=120)
            mock_release.assert_called_once_with("prefetch:AAPL")
            mock_get_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_background_prefetch_skips_when_lock_not_acquired(self):
        """Test that background prefetch skips when lock not acquired."""
        from src.api.routes.analysis import _background_prefetch

        with patch("src.api.routes.analysis.acquire_scrape_lock") as mock_acquire, \
             patch("src.api.routes.analysis.release_scrape_lock") as mock_release, \
             patch("src.api.routes.analysis.get_financial_data") as mock_get_data:
            mock_acquire.return_value = False

            await _background_prefetch("AAPL", MagicMock())

            mock_acquire.assert_called_once()
            mock_release.assert_not_called()
            mock_get_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_background_prefetch_releases_lock_on_error(self):
        """Test that background prefetch releases lock even on error."""
        from src.api.routes.analysis import _background_prefetch

        with patch("src.api.routes.analysis.acquire_scrape_lock") as mock_acquire, \
             patch("src.api.routes.analysis.release_scrape_lock") as mock_release, \
             patch("src.api.routes.analysis.get_financial_data") as mock_get_data:
            mock_acquire.return_value = True
            mock_get_data.side_effect = Exception("Fetch error")

            with pytest.raises(Exception):
                await _background_prefetch("AAPL", MagicMock())

            mock_release.assert_called_once_with("prefetch:AAPL")


class TestAnalysisStatus:
    """Test suite for analysis status endpoint."""

    @pytest.mark.asyncio
    async def test_get_analysis_status_returns_cached_status(self):
        """Test that get_analysis_status returns correct status."""
        from src.api.routes.analysis import get_analysis_status

        with patch("src.api.routes.analysis.cache_get") as mock_cache_get, \
             patch("src.api.routes.analysis._is_prefetching") as mock_is_prefetching:
            mock_cache_get.return_value = {"some": "data"}
            mock_is_prefetching.return_value = False

            # Mock db session
            mock_db = MagicMock()

            result = await get_analysis_status("AAPL", db=mock_db)

            assert result["symbol"] == "AAPL"
            assert result["cached"] is True
            assert result["fetching"] is False

    @pytest.mark.asyncio
    async def test_get_analysis_status_shows_fetching(self):
        """Test that get_analysis_status shows fetching status."""
        from src.api.routes.analysis import get_analysis_status

        with patch("src.api.routes.analysis.cache_get") as mock_cache_get, \
             patch("src.api.routes.analysis._is_prefetching") as mock_is_prefetching:
            mock_cache_get.return_value = None
            mock_is_prefetching.return_value = True

            mock_db = MagicMock()

            result = await get_analysis_status("AAPL", db=mock_db)

            assert result["symbol"] == "AAPL"
            assert result["cached"] is False
            assert result["fetching"] is True
