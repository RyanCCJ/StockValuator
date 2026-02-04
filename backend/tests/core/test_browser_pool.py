"""Unit tests for browser pool."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from src.core.browser_pool import (
    BrowserPool,
    BrowserInstance,
    BrowserContextManager,
    get_browser_pool,
    close_browser_pool,
)


class TestBrowserInstance:
    """Test suite for BrowserInstance dataclass."""

    def test_browser_instance_defaults(self):
        """Test BrowserInstance default values."""
        mock_browser = MagicMock()
        instance = BrowserInstance(browser=mock_browser)

        assert instance.browser == mock_browser
        assert instance.usage_count == 0
        assert instance.is_healthy is True


class TestBrowserContextManager:
    """Test suite for BrowserContextManager."""

    @pytest.mark.asyncio
    async def test_context_manager_acquires_and_releases(self):
        """Test that context manager properly acquires and releases."""
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire = AsyncMock(return_value=(mock_browser, mock_context))
        mock_pool.release = AsyncMock()

        manager = BrowserContextManager(pool=mock_pool)

        async with manager as (browser, context):
            assert browser == mock_browser
            assert context == mock_context
            mock_pool.acquire.assert_called_once()

        mock_pool.release.assert_called_once_with(mock_browser, mock_context)

    @pytest.mark.asyncio
    async def test_context_manager_releases_on_exception(self):
        """Test that context manager releases even on exception."""
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire = AsyncMock(return_value=(mock_browser, mock_context))
        mock_pool.release = AsyncMock()

        manager = BrowserContextManager(pool=mock_pool)

        with pytest.raises(ValueError):
            async with manager as (browser, context):
                raise ValueError("Test error")

        mock_pool.release.assert_called_once_with(mock_browser, mock_context)


class TestGlobalBrowserPool:
    """Test suite for global browser pool functions."""

    @pytest.fixture(autouse=True)
    def reset_global_pool(self):
        """Reset the global pool before each test."""
        import src.core.browser_pool as bp_module
        bp_module._browser_pool = None
        yield
        bp_module._browser_pool = None

    def test_get_browser_pool_creates_pool(self):
        """Test that get_browser_pool creates a pool on first call."""
        pool = get_browser_pool()

        assert pool is not None
        assert isinstance(pool, BrowserPool)

    def test_get_browser_pool_returns_same_pool(self):
        """Test that get_browser_pool returns the same pool instance."""
        pool1 = get_browser_pool()
        pool2 = get_browser_pool()

        assert pool1 is pool2

    @pytest.mark.asyncio
    async def test_close_browser_pool_clears_global(self):
        """Test that close_browser_pool clears the global pool."""
        import src.core.browser_pool as bp_module

        # Create a mock pool
        mock_pool = AsyncMock()
        bp_module._browser_pool = mock_pool

        await close_browser_pool()

        mock_pool.close_all.assert_called_once()
        assert bp_module._browser_pool is None

    @pytest.mark.asyncio
    async def test_close_browser_pool_handles_none(self):
        """Test that close_browser_pool handles None gracefully."""
        import src.core.browser_pool as bp_module
        bp_module._browser_pool = None

        # Should not raise
        await close_browser_pool()

        assert bp_module._browser_pool is None


class TestBrowserPoolUnit:
    """Unit tests for BrowserPool class that don't require actual Playwright."""

    def test_browser_pool_initial_state(self):
        """Test BrowserPool initial state."""
        pool = BrowserPool(max_browsers=3, max_usage_per_browser=100)

        assert pool.max_browsers == 3
        assert pool.max_usage_per_browser == 100
        assert pool._initialized is False
        assert len(pool._browsers) == 0

    def test_browser_pool_get_status_before_init(self):
        """Test get_status before pool is initialized."""
        pool = BrowserPool(max_browsers=3)

        status = pool.get_status()

        assert status["max_browsers"] == 3
        assert status["total"] == 0
        assert len(status["browsers"]) == 0
