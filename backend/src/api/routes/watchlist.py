"""Watchlist API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.api.deps import CurrentUser, DbSession
from src.schemas.watchlist import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CategoryWithItems,
    WatchlistItemCreate,
    WatchlistItemResponse,
    WatchlistItemUpdate,
    WatchlistResponse,
)
from src.services.watchlist_service import (
    create_category,
    create_watchlist_item,
    delete_category,
    delete_watchlist_item,
    get_categories_by_user,
    get_category_by_id,
    get_uncategorized_items,
    get_watchlist_item_by_id,
    get_watchlist_item_by_symbol,
    update_category,
    update_watchlist_item,
)

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


# Watchlist overview
@router.get("", response_model=WatchlistResponse)
async def get_watchlist(current_user: CurrentUser, db: DbSession):
    """Get the full watchlist with categories and items."""
    categories = await get_categories_by_user(db, current_user.id)
    uncategorized = await get_uncategorized_items(db, current_user.id)

    return WatchlistResponse(
        categories=[
            CategoryWithItems(
                id=cat.id,
                user_id=cat.user_id,
                name=cat.name,
                created_at=cat.created_at,
                items=[WatchlistItemResponse.model_validate(item) for item in cat.watchlist_items],
            )
            for cat in categories
        ],
        uncategorized=[WatchlistItemResponse.model_validate(item) for item in uncategorized],
    )


# Category endpoints
@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_new_category(
    data: CategoryCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Create a new category."""
    category = await create_category(db, current_user.id, data)
    await db.commit()
    return CategoryResponse.model_validate(category)


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_existing_category(
    category_id: UUID,
    data: CategoryUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Update a category."""
    category = await get_category_by_id(db, category_id, current_user.id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    updated = await update_category(db, category, data)
    await db.commit()
    return CategoryResponse.model_validate(updated)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_category(
    category_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Delete a category (items become uncategorized)."""
    category = await get_category_by_id(db, category_id, current_user.id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    await delete_category(db, category)
    await db.commit()


# Watchlist item endpoints
@router.post("/items", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_watchlist_item(
    data: WatchlistItemCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Add a stock to the watchlist."""
    # Check if already exists
    existing = await get_watchlist_item_by_symbol(db, data.symbol, current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{data.symbol.upper()} is already in your watchlist",
        )

    item = await create_watchlist_item(db, current_user.id, data)
    await db.commit()
    return WatchlistItemResponse.model_validate(item)


@router.put("/items/{item_id}", response_model=WatchlistItemResponse)
async def update_existing_item(
    item_id: UUID,
    data: WatchlistItemUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Update a watchlist item (e.g., change category)."""
    item = await get_watchlist_item_by_id(db, item_id, current_user.id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    updated = await update_watchlist_item(db, item, data)
    await db.commit()
    return WatchlistItemResponse.model_validate(updated)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_watchlist_item(
    item_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Remove a stock from the watchlist."""
    item = await get_watchlist_item_by_id(db, item_id, current_user.id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    await delete_watchlist_item(db, item)
    await db.commit()
