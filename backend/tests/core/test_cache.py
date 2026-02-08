"""Unit tests for Redis connection pool."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.cache import (
    get_redis_pool,
    get_redis,
    close_redis_pool,
    cache_get,
    cache_set,
    cache_delete,
    acquire_scrape_lock,
    release_scrape_lock,
    ScrapeLocker,
)


class TestRedisConnectionPool:
    """Test suite for Redis connection pool lifecycle."""

    @pytest.fixture(autouse=True)
    def reset_pool(self):
        """Reset the global pool before each test."""
        import src.core.cache as cache_module
        cache_module._pool = None
        yield
        cache_module._pool = None

    @pytest.mark.asyncio
    async def test_get_redis_pool_creates_pool_on_first_call(self):
        """Test that get_redis_pool creates a pool on first call."""
        with patch("src.core.cache.ConnectionPool") as MockPool:
            mock_pool = MagicMock()
            MockPool.from_url.return_value = mock_pool

            pool = await get_redis_pool()

            assert pool == mock_pool
            MockPool.from_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_redis_pool_returns_same_pool_on_subsequent_calls(self):
        """Test that get_redis_pool returns the same pool instance."""
        with patch("src.core.cache.ConnectionPool") as MockPool:
            mock_pool = MagicMock()
            MockPool.from_url.return_value = mock_pool

            pool1 = await get_redis_pool()
            pool2 = await get_redis_pool()

            assert pool1 is pool2
            # Should only be called once (lazy initialization)
            MockPool.from_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_redis_returns_client_with_pool(self):
        """Test that get_redis returns a Redis client using the pool."""
        with patch("src.core.cache.ConnectionPool") as MockPool, \
             patch("src.core.cache.redis.Redis") as MockRedis:
            mock_pool = MagicMock()
            MockPool.from_url.return_value = mock_pool

            client = await get_redis()

            MockRedis.assert_called_once_with(connection_pool=mock_pool)

    @pytest.mark.asyncio
    async def test_close_redis_pool_disconnects_and_clears(self):
        """Test that close_redis_pool properly cleans up."""
        import src.core.cache as cache_module

        mock_pool = AsyncMock()
        cache_module._pool = mock_pool

        await close_redis_pool()

        mock_pool.disconnect.assert_called_once()
        assert cache_module._pool is None

    @pytest.mark.asyncio
    async def test_close_redis_pool_handles_none_pool(self):
        """Test that close_redis_pool handles None pool gracefully."""
        import src.core.cache as cache_module
        cache_module._pool = None

        # Should not raise
        await close_redis_pool()

        assert cache_module._pool is None


class TestCacheOperations:
    """Test suite for cache operations."""

    @pytest.mark.asyncio
    async def test_cache_get_returns_parsed_json(self):
        """Test that cache_get returns parsed JSON."""
        with patch("src.core.cache.get_redis") as mock_get_redis:
            mock_client = AsyncMock()
            mock_client.get.return_value = b'{"key": "value"}'
            mock_get_redis.return_value = mock_client

            result = await cache_get("test_key")

            assert result == {"key": "value"}
            mock_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_cache_get_returns_none_for_missing_key(self):
        """Test that cache_get returns None for missing keys."""
        with patch("src.core.cache.get_redis") as mock_get_redis:
            mock_client = AsyncMock()
            mock_client.get.return_value = None
            mock_get_redis.return_value = mock_client

            result = await cache_get("missing_key")

            assert result is None

    @pytest.mark.asyncio
    async def test_cache_set_stores_json(self):
        """Test that cache_set stores JSON with TTL."""
        with patch("src.core.cache.get_redis") as mock_get_redis:
            mock_client = AsyncMock()
            mock_get_redis.return_value = mock_client

            await cache_set("test_key", {"data": 123}, ttl=60)

            mock_client.set.assert_called_once()
            call_args = mock_client.set.call_args
            assert call_args[0][0] == "test_key"
            assert call_args[1]["ex"] == 60

    @pytest.mark.asyncio
    async def test_cache_delete_removes_key(self):
        """Test that cache_delete removes the key."""
        with patch("src.core.cache.get_redis") as mock_get_redis:
            mock_client = AsyncMock()
            mock_get_redis.return_value = mock_client

            await cache_delete("test_key")

            mock_client.delete.assert_called_once_with("test_key")


class TestDistributedLocking:
    """Test suite for distributed locking mechanism."""

    @pytest.mark.asyncio
    async def test_acquire_scrape_lock_success(self):
        """Test successful lock acquisition."""
        with patch("src.core.cache.get_redis") as mock_get_redis:
            mock_client = AsyncMock()
            mock_client.set.return_value = True  # Lock acquired
            mock_get_redis.return_value = mock_client

            result = await acquire_scrape_lock("AAPL", ttl=60)

            assert result is True
            mock_client.set.assert_called_once_with(
                "lock:scrape:AAPL", "1", nx=True, ex=60
            )

    @pytest.mark.asyncio
    async def test_acquire_scrape_lock_already_locked(self):
        """Test lock acquisition when already locked."""
        with patch("src.core.cache.get_redis") as mock_get_redis:
            mock_client = AsyncMock()
            mock_client.set.return_value = None  # Lock not acquired
            mock_get_redis.return_value = mock_client

            result = await acquire_scrape_lock("AAPL")

            assert result is False

    @pytest.mark.asyncio
    async def test_release_scrape_lock(self):
        """Test lock release."""
        with patch("src.core.cache.get_redis") as mock_get_redis:
            mock_client = AsyncMock()
            mock_get_redis.return_value = mock_client

            await release_scrape_lock("AAPL")

            mock_client.delete.assert_called_once_with("lock:scrape:AAPL")

    @pytest.mark.asyncio
    async def test_scrape_locker_context_manager_acquires_and_releases(self):
        """Test ScrapeLocker context manager."""
        with patch("src.core.cache.acquire_scrape_lock") as mock_acquire, \
             patch("src.core.cache.release_scrape_lock") as mock_release:
            mock_acquire.return_value = True

            async with ScrapeLocker("AAPL") as acquired:
                assert acquired is True
                mock_acquire.assert_called_once_with("AAPL", 60)

            mock_release.assert_called_once_with("AAPL")

    @pytest.mark.asyncio
    async def test_scrape_locker_does_not_release_if_not_acquired(self):
        """Test ScrapeLocker doesn't release if lock wasn't acquired."""
        with patch("src.core.cache.acquire_scrape_lock") as mock_acquire, \
             patch("src.core.cache.release_scrape_lock") as mock_release:
            mock_acquire.return_value = False

            async with ScrapeLocker("AAPL") as acquired:
                assert acquired is False

            mock_release.assert_not_called()

    @pytest.mark.asyncio
    async def test_scrape_locker_uppercases_symbol(self):
        """Test that ScrapeLocker uppercases the symbol."""
        locker = ScrapeLocker("aapl")
        assert locker.symbol == "AAPL"
