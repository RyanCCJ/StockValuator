"""
Script to flush Redis cache.

This script connects to the Redis instance defined in environment variables
and executes a FLUSHDB command. This removes ALL keys in the current database.

Use this when:
- You want to force clear all API response caches.
- You want to clear scraping locks or cached HTML content.
- You changed data structures and need to invalidate old cached objects.

Usage:
    python clear_redis_cache.py
"""

import asyncio
import logging

from src.core.cache import get_redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def clear_redis_cache():
    print("🧹 Starting Redis cache cleanup...")
    
    try:
        redis = await get_redis()
        await redis.flushdb()
        await redis.aclose()
        print("✅ Successfully flushed Redis cache.")
        print("   All temporary keys, scraping caches, and API caches have been removed.")
        
    except Exception as e:
        print(f"❌ Error flushing Redis: {e}")
        logger.error("Redis cleanup failed", exc_info=True)


if __name__ == "__main__":
    asyncio.run(clear_redis_cache())
