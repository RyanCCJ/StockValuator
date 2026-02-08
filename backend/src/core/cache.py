"""Redis cache connection and utilities."""

import json
import logging
from typing import Any

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from src.core.config import get_settings

logger = logging.getLogger(__name__)

# Global connection pool (lazy initialization)
_pool: ConnectionPool | None = None


async def get_redis_pool() -> ConnectionPool:
    """Get or create the Redis connection pool (lazy initialization)."""
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = ConnectionPool.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            decode_responses=False,
        )
        logger.info(
            f"Redis connection pool created (max_connections={settings.redis_max_connections})"
        )
    return _pool


async def get_redis() -> redis.Redis:
    """Get Redis connection from pool."""
    pool = await get_redis_pool()
    return redis.Redis(connection_pool=pool)


async def close_redis_pool() -> None:
    """Close the Redis connection pool for graceful shutdown."""
    global _pool
    if _pool is not None:
        await _pool.disconnect()
        _pool = None
        logger.info("Redis connection pool closed")


async def cache_get(key: str) -> Any | None:
    """Get value from cache."""
    client = await get_redis()
    value = await client.get(key)
    if value:
        return json.loads(value)
    return None


async def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    """Set value in cache with optional TTL."""
    settings = get_settings()
    client = await get_redis()
    ttl = ttl or settings.cache_ttl_seconds
    await client.set(key, json.dumps(value), ex=ttl)


async def cache_delete(key: str) -> None:
    """Delete value from cache."""
    client = await get_redis()
    await client.delete(key)


# Distributed Locking for Scrape Deduplication


async def acquire_scrape_lock(symbol: str, ttl: int = 60) -> bool:
    """
    Acquire a distributed lock for scraping a symbol.

    Uses Redis SET NX EX for atomic lock acquisition.

    Args:
        symbol: The stock symbol to lock.
        ttl: Lock timeout in seconds (default: 60).

    Returns:
        True if lock acquired, False if already locked.
    """
    client = await get_redis()
    key = f"lock:scrape:{symbol.upper()}"
    result = await client.set(key, "1", nx=True, ex=ttl)
    if result:
        logger.debug(f"Acquired scrape lock for {symbol}")
    return bool(result)


async def release_scrape_lock(symbol: str) -> None:
    """
    Release a distributed lock for scraping a symbol.

    Args:
        symbol: The stock symbol to unlock.
    """
    client = await get_redis()
    key = f"lock:scrape:{symbol.upper()}"
    await client.delete(key)
    logger.debug(f"Released scrape lock for {symbol}")


class ScrapeLocker:
    """
    Async context manager for automatic scrape lock management.

    Usage:
        async with ScrapeLocker("AAPL") as acquired:
            if acquired:
                # Perform scraping
                ...
            else:
                # Another request is already scraping, wait or skip
                ...
    """

    def __init__(self, symbol: str, ttl: int = 60):
        self.symbol = symbol.upper()
        self.ttl = ttl
        self._acquired = False

    async def __aenter__(self) -> bool:
        self._acquired = await acquire_scrape_lock(self.symbol, self.ttl)
        return self._acquired

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._acquired:
            await release_scrape_lock(self.symbol)
