"""
Script to flush Redis cache.

This script connects to the Redis instance and clears cached data.
Supports clearing all keys or specific key patterns.

Use this when:
- You want to force clear all API response caches
- You want to clear scraping locks or cached HTML content
- You changed data structures and need to invalidate old cached objects
- You want to clear specific scraper caches

Usage:
    python clear_redis_cache.py              # Flush entire Redis database
    python clear_redis_cache.py --pattern X  # Delete keys matching pattern
    python clear_redis_cache.py --list       # List common cache patterns
"""

import argparse
import asyncio
import logging

from src.core.cache import get_redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Common cache patterns
CACHE_PATTERNS = {
    "scraper:*": "All scraper caches (ROIC, Finviz, Shiller PE)",
    "scraper:shiller_pe:*": "Shiller PE ratio cache",
    "scraper:finviz:*": "Finviz scraper cache",
    "scraper:roic:*": "ROIC.ai scraper cache",
    "market:*": "Market data caches",
    "analysis:*": "Stock analysis caches",
}


async def flush_all():
    """Flush entire Redis database."""
    print("🧹 Starting Redis cache cleanup...")

    try:
        redis = await get_redis()
        await redis.flushdb()
        await redis.aclose()
        print("✅ Successfully flushed entire Redis cache.")
        print("   All temporary keys, scraping caches, and API caches have been removed.")

    except Exception as e:
        print(f"❌ Error flushing Redis: {e}")
        logger.error("Redis cleanup failed", exc_info=True)


async def delete_pattern(pattern: str):
    """Delete keys matching a pattern."""
    print(f"🧹 Deleting Redis keys matching pattern: {pattern}")

    try:
        redis = await get_redis()

        # Scan for keys matching the pattern
        cursor = 0
        total_deleted = 0

        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)
            if keys:
                deleted = await redis.delete(*keys)
                total_deleted += deleted
                print(f"   - Deleted {deleted} keys")

            if cursor == 0:
                break

        await redis.aclose()
        print(f"✅ Successfully deleted {total_deleted} keys matching '{pattern}'.")

    except Exception as e:
        print(f"❌ Error deleting Redis keys: {e}")
        logger.error("Redis cleanup failed", exc_info=True)


def list_patterns():
    """Print common cache patterns."""
    print("📋 Common cache patterns:")
    for pattern, description in CACHE_PATTERNS.items():
        print(f"   - {pattern}: {description}")


def main():
    parser = argparse.ArgumentParser(description="Clear Redis cache")
    parser.add_argument(
        "--pattern", "-p",
        type=str,
        help="Delete keys matching this pattern (e.g., 'scraper:*')",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List common cache patterns",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Flush entire Redis database (default if no --pattern specified)",
    )

    args = parser.parse_args()

    if args.list:
        list_patterns()
        return

    if args.pattern:
        asyncio.run(delete_pattern(args.pattern))
    else:
        asyncio.run(flush_all())


if __name__ == "__main__":
    main()
