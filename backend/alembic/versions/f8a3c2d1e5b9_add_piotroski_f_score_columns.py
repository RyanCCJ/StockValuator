"""add piotroski f-score columns

Revision ID: f8a3c2d1e5b9
Revises: 97cb97f58216
Create Date: 2026-01-29 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'f8a3c2d1e5b9'
down_revision: Union[str, None] = '97cb97f58216'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('financial_data', sa.Column('return_on_assets_history', JSONB, nullable=True))
    op.add_column('financial_data', sa.Column('cash_flow_per_share_history', JSONB, nullable=True))
    op.add_column('financial_data', sa.Column('gross_margin_history', JSONB, nullable=True))
    op.add_column('financial_data', sa.Column('long_term_debt_to_total_assets_history', JSONB, nullable=True))
    op.add_column('financial_data', sa.Column('current_ratio_history', JSONB, nullable=True))
    op.add_column('financial_data', sa.Column('common_equity_to_total_assets_history', JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column('financial_data', 'common_equity_to_total_assets_history')
    op.drop_column('financial_data', 'current_ratio_history')
    op.drop_column('financial_data', 'long_term_debt_to_total_assets_history')
    op.drop_column('financial_data', 'gross_margin_history')
    op.drop_column('financial_data', 'cash_flow_per_share_history')
    op.drop_column('financial_data', 'return_on_assets_history')
