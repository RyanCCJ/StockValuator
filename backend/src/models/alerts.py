"""Price alert and stock fundamentals models for technical analysis feature."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func, BigInteger
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin


class AlertStatus(str, enum.Enum):
    """Status of a price alert."""

    ACTIVE = "active"
    TRIGGERED = "triggered"
    INACTIVE = "inactive"


class PriceAlert(Base, UUIDMixin, TimestampMixin):
    """User-defined price alert for a stock."""

    __tablename__ = "price_alerts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    target_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    initial_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus), default=AlertStatus.ACTIVE, nullable=False, index=True
    )
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="price_alerts")

    def __repr__(self) -> str:
        return f"<PriceAlert {self.symbol} target={self.target_price} status={self.status}>"


class StockFundamentals(Base, UUIDMixin):
    """Cached fundamental data for a stock."""

    __tablename__ = "stock_fundamentals"

    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    pe_ratio: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    dividend_yield: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    market_cap: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    eps: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    beta: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    fifty_two_week_high: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    fifty_two_week_low: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    major_shareholders: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<StockFundamentals {self.symbol} PE={self.pe_ratio}>"


# Forward reference for User relationship
from src.models.user import User  # noqa: E402, F401
