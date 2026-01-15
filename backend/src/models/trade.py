"""Trade model for stock transactions."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin


class TradeType(str, enum.Enum):
    """Trade action types."""

    BUY = "buy"
    SELL = "sell"


class Trade(Base, UUIDMixin, TimestampMixin):
    """Stock trade record model."""

    __tablename__ = "trades"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    type: Mapped[TradeType] = mapped_column(Enum(TradeType), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    fees: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    notes: Mapped[str | None] = mapped_column(String(5000), nullable=True)  # Trading journal/notes

    # Relationships
    user: Mapped["User"] = relationship(back_populates="trades")


# Forward reference
from src.models.user import User  # noqa: E402, F401
