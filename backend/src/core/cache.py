"""Redis cache connection and utilities."""

import json
from typing import Any

import redis.asyncio as redis

from src.core.config import get_settings

settings = get_settings()

# Redis connection pool
redis_pool = redis.ConnectionPool.from_url(settings.redis_url)


async def get_redis() -> redis.Redis:
    """Get Redis connection."""
    return redis.Redis(connection_pool=redis_pool)


async def cache_get(key: str) -> Any | None:
    """Get value from cache."""
    client = await get_redis()
    try:
        value = await client.get(key)
        if value:
            return json.loads(value)
        return None
    finally:
        await client.aclose()


async def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    """Set value in cache with optional TTL."""
    client = await get_redis()
    try:
        ttl = ttl or settings.cache_ttl_seconds
        await client.set(key, json.dumps(value), ex=ttl)
    finally:
        await client.aclose()


async def cache_delete(key: str) -> None:
    """Delete value from cache."""
    client = await get_redis()
    try:
        await client.delete(key)
    finally:
        await client.aclose()
