"""Cash transaction model for deposits and withdrawals."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin


class CashTransaction(Base, UUIDMixin, TimestampMixin):
    """Cash deposit/withdrawal record model."""

    __tablename__ = "cash_transactions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Deposit", "Qualified Dividend"
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)  # Positive = money in, Negative = money out
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="cash_transactions")


# Forward reference
from src.models.user import User  # noqa: E402, F401
