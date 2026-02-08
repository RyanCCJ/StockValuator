"""Add market_cycle_snapshots table.

Revision ID: a1b2c3d4e5f6
Revises: f8a3c2d1e5b9
Create Date: 2026-02-02

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "f8a3c2d1e5b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_cycle_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("snapshot_date", sa.Date(), nullable=False, unique=True, index=True),
        # Raw Indicators - Trend
        sa.Column("sp500_price", sa.Float(), nullable=True),
        sa.Column("sp500_ma200", sa.Float(), nullable=True),
        # Raw Indicators - Valuation
        sa.Column("shiller_pe", sa.Float(), nullable=True),
        # Raw Indicators - Recession (Yield Curve)
        sa.Column("treasury_10y", sa.Float(), nullable=True),
        sa.Column("treasury_3m", sa.Float(), nullable=True),
        sa.Column("yield_spread", sa.Float(), nullable=True),
        # Raw Indicators - Fear
        sa.Column("vix", sa.Float(), nullable=True),
        # Raw Indicators - Breadth
        sa.Column("breadth_ma5", sa.Float(), nullable=True),
        sa.Column("breadth_ma20", sa.Float(), nullable=True),
        # Computed Scores
        sa.Column("total_score", sa.Integer(), nullable=True),
        sa.Column("phase", sa.String(50), nullable=True),
        sa.Column("phase_number", sa.Integer(), nullable=True),
        sa.Column("risk_level", sa.String(20), nullable=True),
        # Market Pulse Data
        sa.Column("djia_price", sa.Float(), nullable=True),
        sa.Column("djia_change_percent", sa.Float(), nullable=True),
        sa.Column("nasdaq_price", sa.Float(), nullable=True),
        sa.Column("nasdaq_change_percent", sa.Float(), nullable=True),
        sa.Column("sp500_change_percent", sa.Float(), nullable=True),
        sa.Column("russell_price", sa.Float(), nullable=True),
        sa.Column("russell_change_percent", sa.Float(), nullable=True),
        # Timestamp
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("market_cycle_snapshots")
