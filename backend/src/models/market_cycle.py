"""Market Cycle Snapshot model for storing daily market cycle data."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class MarketCycleSnapshot(Base, TimestampMixin):
    """
    Daily snapshot of market cycle indicators and computed scores.

    Stores raw indicator values and calculated phase/score for historical tracking.
    """

    __tablename__ = "market_cycle_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    snapshot_date: Mapped[date] = mapped_column(
        Date, nullable=False, unique=True, index=True
    )

    # Raw Indicators - Trend
    sp500_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    sp500_ma200: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Raw Indicators - Valuation
    shiller_pe: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Raw Indicators - Recession (Yield Curve)
    treasury_10y: Mapped[float | None] = mapped_column(Float, nullable=True)
    treasury_3m: Mapped[float | None] = mapped_column(Float, nullable=True)
    yield_spread: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Raw Indicators - Fear
    vix: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Raw Indicators - Breadth (Nasdaq Net Issues)
    breadth_ma5: Mapped[float | None] = mapped_column(Float, nullable=True)
    breadth_ma20: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Computed Scores
    total_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phase: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phase_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Market Pulse Data (for frontend display)
    djia_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    djia_change_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    nasdaq_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    nasdaq_change_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    sp500_change_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    russell_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    russell_change_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
