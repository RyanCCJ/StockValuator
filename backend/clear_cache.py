import asyncio
from sqlalchemy import text
from src.core.database import async_session_maker

async def clear_fundamentals():
    print("🧹 Clearing stock_fundamentals table...")
    async with async_session_maker() as session:
        try:
            await session.execute(text("DELETE FROM stock_fundamentals"))
            await session.commit()
            print("✅ Successfully cleared cache. Next fetch will populate new fields.")
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")

if __name__ == "__main__":
    asyncio.run(clear_fundamentals())
