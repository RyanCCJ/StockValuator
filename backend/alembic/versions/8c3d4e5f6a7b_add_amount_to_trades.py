"""Add amount column to trades table.

Revision ID: 8c3d4e5f6a7b
Revises: 7b2c3d4e5f6a
Create Date: 2026-02-06

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8c3d4e5f6a7b"
down_revision: str | None = "7b2c3d4e5f6a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add amount column to trades table."""
    op.add_column(
        "trades",
        sa.Column("amount", sa.Numeric(precision=18, scale=6), nullable=True),
    )


def downgrade() -> None:
    """Remove amount column from trades table."""
    op.drop_column("trades", "amount")
