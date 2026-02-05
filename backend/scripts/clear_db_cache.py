"""
Script to clear PostgreSQL cache tables.

This script clears cached data from the database to force the application
to re-fetch data from external sources.

Tables cleared:
- financial_data: Historical scraped financial metrics
- stock_fundamentals: Derived fundamental data for browsing/filtering
- ai_score_cache: Cached AI analysis results
- market_cycle_snapshots: Daily market cycle indicator snapshots

Usage:
    python clear_db_cache.py              # Clear all cache tables
    python clear_db_cache.py --table X    # Clear specific table only
    python clear_db_cache.py --list       # List available tables
"""

import argparse
import asyncio
import logging

from sqlalchemy import text

from src.core.database import async_session_maker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# All cache tables that can be cleared
CACHE_TABLES = {
    "financial_data": "Historical scraped financial metrics",
    "stock_fundamentals": "Derived fundamental data for browsing/filtering",
    "ai_score_cache": "Cached AI analysis results",
    "market_cycle_snapshots": "Daily market cycle indicator snapshots",
}


async def clear_tables(tables: list[str]):
    """Clear specified tables from the database."""
    print("🧹 Starting PostgreSQL cache cleanup...")

    async with async_session_maker() as session:
        try:
            for table in tables:
                if table not in CACHE_TABLES:
                    print(f"   ⚠️  Unknown table: {table}, skipping...")
                    continue
                print(f"   - Clearing table: {table}...")
                result = await session.execute(text(f"DELETE FROM {table}"))
                print(f"     Deleted {result.rowcount} rows")

            await session.commit()
            print("✅ Successfully cleared database cache.")
            print("   The application will fetch fresh data on the next request.")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error clearing database cache: {e}")
            logger.error("Database cleanup failed", exc_info=True)


def list_tables():
    """Print available cache tables."""
    print("📋 Available cache tables:")
    for table, description in CACHE_TABLES.items():
        print(f"   - {table}: {description}")


def main():
    parser = argparse.ArgumentParser(description="Clear PostgreSQL cache tables")
    parser.add_argument(
        "--table", "-t",
        type=str,
        action="append",
        help="Specific table(s) to clear. Can be used multiple times.",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available cache tables",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Clear all cache tables (default if no --table specified)",
    )

    args = parser.parse_args()

    if args.list:
        list_tables()
        return

    if args.table:
        tables = args.table
    else:
        tables = list(CACHE_TABLES.keys())

    asyncio.run(clear_tables(tables))


if __name__ == "__main__":
    main()
