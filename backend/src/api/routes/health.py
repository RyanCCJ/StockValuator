"""Health check endpoints for monitoring pool status."""

from typing import Any

from fastapi import APIRouter

from src.core.cache import get_redis_pool
from src.core.database import engine
from src.core.browser_pool import get_browser_pool
from src.core.yfinance_async import get_yf_executor

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/pools")
async def get_pool_status() -> dict[str, Any]:
    """
    Get status of all connection pools and executors.

    Returns status for:
    - Redis connection pool
    - PostgreSQL connection pool
    - Browser pool
    - yfinance ThreadPoolExecutor
    """
    status = {
        "redis": await _get_redis_status(),
        "postgresql": _get_postgresql_status(),
        "browser": _get_browser_status(),
        "yfinance": _get_yfinance_status(),
    }

    # Determine overall health
    all_healthy = all(
        pool.get("healthy", True)
        for pool in status.values()
        if isinstance(pool, dict)
    )

    return {
        "status": "healthy" if all_healthy else "degraded",
        "pools": status,
    }


async def _get_redis_status() -> dict[str, Any]:
    """Get Redis connection pool status."""
    try:
        pool = await get_redis_pool()
        # ConnectionPool doesn't expose all stats directly, but we can get some
        return {
            "healthy": True,
            "max_connections": pool.max_connections,
            # Note: redis-py ConnectionPool doesn't expose current connection count
            # We can only confirm the pool exists and is configured
            "configured": True,
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
        }


def _get_postgresql_status() -> dict[str, Any]:
    """Get PostgreSQL connection pool status."""
    try:
        pool = engine.pool
        return {
            "healthy": True,
            "pool_size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "checked_in": pool.checkedin(),
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
        }


def _get_browser_status() -> dict[str, Any]:
    """Get browser pool status."""
    try:
        pool = get_browser_pool()
        return pool.get_status()
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
        }


def _get_yfinance_status() -> dict[str, Any]:
    """Get yfinance ThreadPoolExecutor status."""
    try:
        executor = get_yf_executor()
        # ThreadPoolExecutor has limited introspection
        return {
            "healthy": True,
            "max_workers": executor._max_workers,
            "thread_name_prefix": executor._thread_name_prefix,
            # _work_queue can give us pending work count
            "pending_tasks": executor._work_queue.qsize(),
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
        }
