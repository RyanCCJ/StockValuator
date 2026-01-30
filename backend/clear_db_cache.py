"""
Script to clear PostgreSQL cache tables.

This script clears the following tables:
1. financial_data: Stores historical scraped financial metrics (e.g., from ROIC.ai, Finviz).
   Clearing this forces the application to re-fetch data from external sources.
2. stock_fundamentals: Stores derived fundamental data used for browsing and filtering.
   Clearing this ensures derived data is rebuilt from fresh financial data.
3. ai_score_cache: Stores cached AI analysis results.
   Clearing this forces re-generation of AI insights.

Usage:
    python clear_db_cache.py
"""

import asyncio
import logging

from sqlalchemy import text

from src.core.database import async_session_maker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def clear_db_cache():
    print("🧹 Starting PostgreSQL cache cleanup...")
    
    tables_to_clear = [
        "financial_data",
        "stock_fundamentals",
        "ai_score_cache"
    ]

    async with async_session_maker() as session:
        try:
            for table in tables_to_clear:
                print(f"   - Clearing table: {table}...")
                await session.execute(text(f"DELETE FROM {table}"))
            
            await session.commit()
            print("✅ Successfully cleared all financial and fundamental data from PostgreSQL.")
            print("   The application will fetch fresh data on the next request.")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error clearing database cache: {e}")
            logger.error("Database cleanup failed", exc_info=True)


if __name__ == "__main__":
    asyncio.run(clear_db_cache())
