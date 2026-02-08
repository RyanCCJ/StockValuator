"""add_quote_type_to_financial_data

Revision ID: 7ba08cc3e439
Revises: 8c3d4e5f6a7b
Create Date: 2026-02-07 00:40:40.614533

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ba08cc3e439'
down_revision: Union[str, Sequence[str], None] = '8c3d4e5f6a7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'financial_data',
        sa.Column('quote_type', sa.String(50), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('financial_data', 'quote_type')
