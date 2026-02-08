"""Replace type enum with action varchar in trades and cash_transactions.

Revision ID: 7b2c3d4e5f6a
Revises: 6af1e5f3a02d
Create Date: 2026-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b2c3d4e5f6a'
down_revision: Union[str, None] = '6af1e5f3a02d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === TRADES TABLE ===
    # 1. Add new action column
    op.add_column('trades', sa.Column('action', sa.String(100), nullable=True))

    # 2. Copy type values to action (capitalize first letter)
    op.execute("""
        UPDATE trades
        SET action = INITCAP(type::text)
    """)

    # 3. Make action not nullable
    op.alter_column('trades', 'action', nullable=False)

    # 4. Drop type column
    op.drop_column('trades', 'type')

    # 5. Drop the enum type
    op.execute("DROP TYPE IF EXISTS tradetype")

    # === CASH_TRANSACTIONS TABLE ===
    # 1. Add new action column
    op.add_column('cash_transactions', sa.Column('action', sa.String(100), nullable=True))

    # 2. Copy type values to action (capitalize first letter)
    op.execute("""
        UPDATE cash_transactions
        SET action = INITCAP(type::text)
    """)

    # 3. Make action not nullable
    op.alter_column('cash_transactions', 'action', nullable=False)

    # 4. Drop type column
    op.drop_column('cash_transactions', 'type')

    # 5. Drop the enum type
    op.execute("DROP TYPE IF EXISTS cashtransactiontype")


def downgrade() -> None:
    # === TRADES TABLE ===
    # 1. Recreate enum type
    op.execute("CREATE TYPE tradetype AS ENUM ('buy', 'sell')")

    # 2. Add type column back
    op.add_column('trades', sa.Column('type', sa.Enum('buy', 'sell', name='tradetype'), nullable=True))

    # 3. Copy action values to type (lowercase, default to 'buy' if unknown)
    op.execute("""
        UPDATE trades
        SET type = CASE
            WHEN LOWER(action) = 'sell' THEN 'sell'::tradetype
            ELSE 'buy'::tradetype
        END
    """)

    # 4. Make type not nullable
    op.alter_column('trades', 'type', nullable=False)

    # 5. Drop action column
    op.drop_column('trades', 'action')

    # === CASH_TRANSACTIONS TABLE ===
    # 1. Recreate enum type
    op.execute("CREATE TYPE cashtransactiontype AS ENUM ('DEPOSIT', 'WITHDRAW', 'DIVIDEND', 'TAX', 'INTEREST', 'FEE')")

    # 2. Add type column back
    op.add_column('cash_transactions', sa.Column('type', sa.Enum('DEPOSIT', 'WITHDRAW', 'DIVIDEND', 'TAX', 'INTEREST', 'FEE', name='cashtransactiontype'), nullable=True))

    # 3. Copy action values to type
    op.execute("""
        UPDATE cash_transactions
        SET type = CASE
            WHEN UPPER(action) = 'WITHDRAW' THEN 'WITHDRAW'::cashtransactiontype
            WHEN UPPER(action) = 'DIVIDEND' THEN 'DIVIDEND'::cashtransactiontype
            WHEN UPPER(action) = 'TAX' THEN 'TAX'::cashtransactiontype
            WHEN UPPER(action) = 'INTEREST' THEN 'INTEREST'::cashtransactiontype
            WHEN UPPER(action) = 'FEE' THEN 'FEE'::cashtransactiontype
            ELSE 'DEPOSIT'::cashtransactiontype
        END
    """)

    # 4. Make type not nullable
    op.alter_column('cash_transactions', 'type', nullable=False)

    # 5. Drop action column
    op.drop_column('cash_transactions', 'action')
