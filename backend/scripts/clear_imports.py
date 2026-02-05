#!/usr/bin/env python3
"""Script to clear imported transactions for testing.

Usage:
    python scripts/clear_imports.py --list
    python scripts/clear_imports.py --user your@email.com
    python scripts/clear_imports.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete, select, func

from src.core.database import async_session_maker
from src.models.cash import CashTransaction
from src.models.trade import Trade
from src.models.user import User


async def clear_all_imports(user_email: str | None = None):
    """Clear all imported transactions.

    Args:
        user_email: If provided, only clear for this user. Otherwise clear all.
    """
    async with async_session_maker() as db:
        if user_email:
            # Get user by email
            result = await db.execute(
                select(User).where(User.email == user_email)
            )
            user = result.scalar_one_or_none()
            if not user:
                print(f"User not found: {user_email}")
                return
            user_id = user.id
            print(f"Clearing data for user: {user_email} (ID: {user_id})")
        else:
            user_id = None
            print("Clearing data for ALL users")

        # Count before deletion
        cash_count_query = select(func.count()).select_from(CashTransaction)
        trade_count_query = select(func.count()).select_from(Trade)

        if user_id:
            cash_count_query = cash_count_query.where(CashTransaction.user_id == user_id)
            trade_count_query = trade_count_query.where(Trade.user_id == user_id)

        cash_count = (await db.execute(cash_count_query)).scalar()
        trade_count = (await db.execute(trade_count_query)).scalar()

        print(f"Found: {cash_count} cash transactions, {trade_count} trades")

        # Confirm
        confirm = input("Are you sure you want to delete? (yes/no): ")
        if confirm.lower() != "yes" and confirm.lower() != "y":
            print("Aborted.")
            return

        # Delete cash transactions
        cash_delete = delete(CashTransaction)
        trade_delete = delete(Trade)

        if user_id:
            cash_delete = cash_delete.where(CashTransaction.user_id == user_id)
            trade_delete = trade_delete.where(Trade.user_id == user_id)

        cash_result = await db.execute(cash_delete)
        trade_result = await db.execute(trade_delete)

        await db.commit()

        print(f"Deleted: {cash_result.rowcount} cash transactions, {trade_result.rowcount} trades")
        print("Done!")


async def list_users():
    """List all users."""
    async with async_session_maker() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()

        print("Users:")
        for user in users:
            # Count transactions
            cash_count = (await db.execute(
                select(func.count()).select_from(CashTransaction)
                .where(CashTransaction.user_id == user.id)
            )).scalar()
            trade_count = (await db.execute(
                select(func.count()).select_from(Trade)
                .where(Trade.user_id == user.id)
            )).scalar()

            print(f"  - {user.email} (ID: {user.id})")
            print(f"    Cash: {cash_count}, Trades: {trade_count}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Clear imported transactions")
    parser.add_argument("--user", "-u", help="User email (optional, clears all if not provided)")
    parser.add_argument("--list", "-l", action="store_true", help="List all users")

    args = parser.parse_args()

    if args.list:
        asyncio.run(list_users())
    else:
        asyncio.run(clear_all_imports(args.user))
