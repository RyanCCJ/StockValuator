"""add_new_cash_transaction_types

Revision ID: 6af1e5f3a02d
Revises: a1b2c3d4e5f6
Create Date: 2026-02-05 03:40:25.109789

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6af1e5f3a02d'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new enum values to cashtransactiontype enum in PostgreSQL
    # SQLAlchemy uses enum member names (uppercase) by default
    op.execute("ALTER TYPE cashtransactiontype ADD VALUE IF NOT EXISTS 'DIVIDEND'")
    op.execute("ALTER TYPE cashtransactiontype ADD VALUE IF NOT EXISTS 'TAX'")
    op.execute("ALTER TYPE cashtransactiontype ADD VALUE IF NOT EXISTS 'INTEREST'")
    op.execute("ALTER TYPE cashtransactiontype ADD VALUE IF NOT EXISTS 'FEE'")


def downgrade() -> None:
    """Downgrade schema."""
    # NOTE: PostgreSQL does not support removing enum values directly.
    # To downgrade, you would need to:
    # 1. Create a new enum type without the new values
    # 2. Update the column to use the new type
    # 3. Drop the old enum type
    # This is intentionally left as a no-op because removing enum values
    # could break existing data if any rows use the new types.
    pass
