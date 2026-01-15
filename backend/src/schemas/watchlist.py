"""Watchlist schemas for API validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# Category schemas
class CategoryBase(BaseModel):
    """Base category schema."""

    name: str = Field(..., min_length=1, max_length=100)


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""

    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""

    name: str | None = Field(None, min_length=1, max_length=100)


class CategoryResponse(CategoryBase):
    """Schema for category response."""

    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# WatchlistItem schemas
class WatchlistItemBase(BaseModel):
    """Base watchlist item schema."""

    symbol: str = Field(..., min_length=1, max_length=20)
    category_id: UUID | None = None


class WatchlistItemCreate(WatchlistItemBase):
    """Schema for creating a watchlist item."""

    pass


class WatchlistItemUpdate(BaseModel):
    """Schema for updating a watchlist item."""

    category_id: UUID | None = None


class WatchlistItemResponse(WatchlistItemBase):
    """Schema for watchlist item response."""

    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class WatchlistItemWithCategory(WatchlistItemResponse):
    """Watchlist item with category info."""

    category: CategoryResponse | None = None


class CategoryWithItems(CategoryResponse):
    """Category with its watchlist items."""

    items: list[WatchlistItemResponse] = []


class WatchlistResponse(BaseModel):
    """Full watchlist response with categories and uncategorized items."""

    categories: list[CategoryWithItems]
    uncategorized: list[WatchlistItemResponse]
