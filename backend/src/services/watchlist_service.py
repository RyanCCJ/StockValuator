"""Watchlist service for CRUD operations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.watchlist import Category, WatchlistItem
from src.schemas.watchlist import CategoryCreate, CategoryUpdate, WatchlistItemCreate, WatchlistItemUpdate


# Category operations
async def get_categories_by_user(db: AsyncSession, user_id: UUID) -> list[Category]:
    """Get all categories for a user with their items."""
    query = (
        select(Category)
        .where(Category.user_id == user_id)
        .options(selectinload(Category.watchlist_items))
        .order_by(Category.name)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_category_by_id(db: AsyncSession, category_id: UUID, user_id: UUID) -> Category | None:
    """Get a specific category by ID."""
    query = select(Category).where(Category.id == category_id, Category.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_category(db: AsyncSession, user_id: UUID, data: CategoryCreate) -> Category:
    """Create a new category."""
    category = Category(user_id=user_id, name=data.name)
    db.add(category)
    await db.flush()
    await db.refresh(category)
    return category


async def update_category(db: AsyncSession, category: Category, data: CategoryUpdate) -> Category:
    """Update a category."""
    if data.name is not None:
        category.name = data.name
    await db.flush()
    await db.refresh(category)
    return category


async def delete_category(db: AsyncSession, category: Category) -> None:
    """Delete a category (items become uncategorized)."""
    # Set all items in this category to uncategorized
    for item in category.watchlist_items:
        item.category_id = None
    await db.delete(category)
    await db.flush()


# WatchlistItem operations
async def get_watchlist_items_by_user(db: AsyncSession, user_id: UUID) -> list[WatchlistItem]:
    """Get all watchlist items for a user."""
    query = (
        select(WatchlistItem)
        .where(WatchlistItem.user_id == user_id)
        .order_by(WatchlistItem.symbol)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_uncategorized_items(db: AsyncSession, user_id: UUID) -> list[WatchlistItem]:
    """Get watchlist items without a category."""
    query = (
        select(WatchlistItem)
        .where(WatchlistItem.user_id == user_id, WatchlistItem.category_id.is_(None))
        .order_by(WatchlistItem.symbol)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_watchlist_item_by_id(
    db: AsyncSession, item_id: UUID, user_id: UUID
) -> WatchlistItem | None:
    """Get a specific watchlist item by ID."""
    query = select(WatchlistItem).where(WatchlistItem.id == item_id, WatchlistItem.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_watchlist_item_by_symbol(
    db: AsyncSession, symbol: str, user_id: UUID
) -> WatchlistItem | None:
    """Get a watchlist item by symbol."""
    query = select(WatchlistItem).where(
        WatchlistItem.symbol == symbol.upper(), WatchlistItem.user_id == user_id
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_watchlist_item(
    db: AsyncSession, user_id: UUID, data: WatchlistItemCreate
) -> WatchlistItem:
    """Create a new watchlist item."""
    item = WatchlistItem(
        user_id=user_id,
        symbol=data.symbol.upper(),
        category_id=data.category_id,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def update_watchlist_item(
    db: AsyncSession, item: WatchlistItem, data: WatchlistItemUpdate
) -> WatchlistItem:
    """Update a watchlist item."""
    if data.category_id is not None:
        item.category_id = data.category_id
    await db.flush()
    await db.refresh(item)
    return item


async def delete_watchlist_item(db: AsyncSession, item: WatchlistItem) -> None:
    """Delete a watchlist item."""
    await db.delete(item)
    await db.flush()
