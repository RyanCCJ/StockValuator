import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class FinancialData(Base, TimestampMixin):
    __tablename__ = "financial_data"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    eps_history: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    revenue_history: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    net_income_history: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    dividend_history: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    dividend_growth_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fcf_history: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    fcf_per_share_history: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    shares_outstanding_history: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    book_value_history: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    total_debt_history: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    cash_history: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    roe_history: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    net_margin_history: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    interest_coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    pe_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    forward_pe: Mapped[float | None] = mapped_column(Float, nullable=True)
    peg_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_to_book: Mapped[float | None] = mapped_column(Float, nullable=True)
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    beta: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class AIScoreCache(Base, TimestampMixin):
    __tablename__ = "ai_score_cache"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    score_type: Mapped[str] = mapped_column(String(50), nullable=False)
    score_value: Mapped[float] = mapped_column(Float, nullable=False)
    breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    prompt_used: Mapped[str | None] = mapped_column(String(5000), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
