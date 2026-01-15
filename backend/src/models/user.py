"""User model for authentication and preferences."""

import enum
import uuid

from sqlalchemy import Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin


class ThemePreference(str, enum.Enum):
    """User theme preference options."""

    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class User(Base, UUIDMixin, TimestampMixin):
    """User account model."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    theme_preference: Mapped[ThemePreference] = mapped_column(
        Enum(ThemePreference),
        default=ThemePreference.SYSTEM,
        nullable=False,
    )
    base_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Relationships
    trades: Mapped[list["Trade"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    cash_transactions: Mapped[list["CashTransaction"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    categories: Mapped[list["Category"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    watchlist_items: Mapped[list["WatchlistItem"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


# Forward references for relationships
from src.models.trade import Trade  # noqa: E402, F401
from src.models.cash import CashTransaction  # noqa: E402, F401
from src.models.watchlist import Category, WatchlistItem  # noqa: E402, F401
