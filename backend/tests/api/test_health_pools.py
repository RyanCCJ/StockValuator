"""Unit tests for health endpoint with pool status."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestHealthPoolsEndpoint:
    """Test suite for /health/pools endpoint."""

    @pytest.mark.asyncio
    async def test_get_pool_status_returns_all_pools(self):
        """Test that get_pool_status returns status for all pools."""
        from src.api.routes.health import get_pool_status

        with patch("src.api.routes.health._get_redis_status") as mock_redis, \
             patch("src.api.routes.health._get_postgresql_status") as mock_pg, \
             patch("src.api.routes.health._get_browser_status") as mock_browser, \
             patch("src.api.routes.health._get_yfinance_status") as mock_yf:

            mock_redis.return_value = {"healthy": True, "max_connections": 50}
            mock_pg.return_value = {"healthy": True, "pool_size": 20}
            mock_browser.return_value = {"available": 3, "in_use": 0}
            mock_yf.return_value = {"healthy": True, "max_workers": 10}

            result = await get_pool_status()

            assert result["status"] == "healthy"
            assert "redis" in result["pools"]
            assert "postgresql" in result["pools"]
            assert "browser" in result["pools"]
            assert "yfinance" in result["pools"]

    @pytest.mark.asyncio
    async def test_get_pool_status_degraded_when_unhealthy(self):
        """Test that status is degraded when a pool is unhealthy."""
        from src.api.routes.health import get_pool_status

        with patch("src.api.routes.health._get_redis_status") as mock_redis, \
             patch("src.api.routes.health._get_postgresql_status") as mock_pg, \
             patch("src.api.routes.health._get_browser_status") as mock_browser, \
             patch("src.api.routes.health._get_yfinance_status") as mock_yf:

            mock_redis.return_value = {"healthy": False, "error": "Connection refused"}
            mock_pg.return_value = {"healthy": True, "pool_size": 20}
            mock_browser.return_value = {"available": 3, "in_use": 0}
            mock_yf.return_value = {"healthy": True, "max_workers": 10}

            result = await get_pool_status()

            assert result["status"] == "degraded"


class TestRedisStatus:
    """Test suite for Redis status helper."""

    @pytest.mark.asyncio
    async def test_get_redis_status_success(self):
        """Test Redis status when pool is healthy."""
        from src.api.routes.health import _get_redis_status

        with patch("src.api.routes.health.get_redis_pool") as mock_get_pool:
            mock_pool = MagicMock()
            mock_pool.max_connections = 50
            mock_get_pool.return_value = mock_pool

            result = await _get_redis_status()

            assert result["healthy"] is True
            assert result["max_connections"] == 50

    @pytest.mark.asyncio
    async def test_get_redis_status_error(self):
        """Test Redis status when pool fails."""
        from src.api.routes.health import _get_redis_status

        with patch("src.api.routes.health.get_redis_pool") as mock_get_pool:
            mock_get_pool.side_effect = Exception("Connection failed")

            result = await _get_redis_status()

            assert result["healthy"] is False
            assert "error" in result


class TestPostgresqlStatus:
    """Test suite for PostgreSQL status helper."""

    def test_get_postgresql_status_success(self):
        """Test PostgreSQL status when engine is healthy."""
        from src.api.routes.health import _get_postgresql_status

        with patch("src.api.routes.health.engine") as mock_engine:
            mock_pool = MagicMock()
            mock_pool.size.return_value = 20
            mock_pool.checkedout.return_value = 5
            mock_pool.overflow.return_value = 0
            mock_pool.checkedin.return_value = 15
            mock_engine.pool = mock_pool

            result = _get_postgresql_status()

            assert result["healthy"] is True
            assert result["pool_size"] == 20
            assert result["checked_out"] == 5
            assert result["overflow"] == 0
            assert result["checked_in"] == 15

    def test_get_postgresql_status_error(self):
        """Test PostgreSQL status when engine fails."""
        from src.api.routes.health import _get_postgresql_status

        with patch("src.api.routes.health.engine") as mock_engine:
            mock_engine.pool = None
            type(mock_engine).pool = property(lambda self: (_ for _ in ()).throw(Exception("Pool error")))

            result = _get_postgresql_status()

            assert result["healthy"] is False
            assert "error" in result


class TestBrowserStatus:
    """Test suite for browser pool status helper."""

    def test_get_browser_status_success(self):
        """Test browser status when pool is healthy."""
        from src.api.routes.health import _get_browser_status

        with patch("src.api.routes.health.get_browser_pool") as mock_get_pool:
            mock_pool = MagicMock()
            mock_pool.get_status.return_value = {
                "available": 3,
                "in_use": 0,
                "total": 0,
                "max_browsers": 3,
            }
            mock_get_pool.return_value = mock_pool

            result = _get_browser_status()

            assert result["available"] == 3
            assert result["in_use"] == 0

    def test_get_browser_status_error(self):
        """Test browser status when pool fails."""
        from src.api.routes.health import _get_browser_status

        with patch("src.api.routes.health.get_browser_pool") as mock_get_pool:
            mock_get_pool.side_effect = Exception("Browser error")

            result = _get_browser_status()

            assert result["healthy"] is False
            assert "error" in result


class TestYfinanceStatus:
    """Test suite for yfinance executor status helper."""

    def test_get_yfinance_status_success(self):
        """Test yfinance status when executor is healthy."""
        from src.api.routes.health import _get_yfinance_status

        with patch("src.api.routes.health.get_yf_executor") as mock_get_executor:
            mock_executor = MagicMock()
            mock_executor._max_workers = 10
            mock_executor._thread_name_prefix = "yfinance"
            mock_executor._work_queue = MagicMock()
            mock_executor._work_queue.qsize.return_value = 0
            mock_get_executor.return_value = mock_executor

            result = _get_yfinance_status()

            assert result["healthy"] is True
            assert result["max_workers"] == 10
            assert result["pending_tasks"] == 0

    def test_get_yfinance_status_error(self):
        """Test yfinance status when executor fails."""
        from src.api.routes.health import _get_yfinance_status

        with patch("src.api.routes.health.get_yf_executor") as mock_get_executor:
            mock_get_executor.side_effect = Exception("Executor error")

            result = _get_yfinance_status()

            assert result["healthy"] is False
            assert "error" in result
