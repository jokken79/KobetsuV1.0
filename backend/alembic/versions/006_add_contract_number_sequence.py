"""add_contract_number_sequence

Revision ID: 006_contract_seq
Revises: 6eb7f275e62b
Create Date: 2025-12-08

This migration adds a counter table for generating contract numbers atomically,
preventing race conditions when multiple contracts are created simultaneously.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006_contract_seq'
down_revision: Union[str, None] = '6eb7f275e62b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create contract number counter table
    # This table stores the last used sequence number per month
    # Using FOR UPDATE row locking ensures atomic increment
    op.create_table(
        'contract_number_counters',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('year_month', sa.String(6), nullable=False, unique=True,
                  comment='Format: YYYYMM (e.g., 202412)'),
        sa.Column('last_sequence', sa.Integer(), nullable=False, default=0,
                  comment='Last used sequence number for this month'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )

    # Create index for fast lookup by year_month
    op.create_index(
        'ix_contract_number_counters_year_month',
        'contract_number_counters',
        ['year_month'],
        unique=True
    )

    # Initialize counter based on existing contracts
    # This ensures we don't generate duplicate numbers for existing data
    op.execute("""
        INSERT INTO contract_number_counters (year_month, last_sequence, created_at, updated_at)
        SELECT
            SUBSTRING(contract_number FROM 5 FOR 6) as year_month,
            MAX(CAST(SUBSTRING(contract_number FROM 12 FOR 4) AS INTEGER)) as last_sequence,
            NOW() as created_at,
            NOW() as updated_at
        FROM kobetsu_keiyakusho
        WHERE contract_number LIKE 'KOB-______-____'
        GROUP BY SUBSTRING(contract_number FROM 5 FOR 6)
        ON CONFLICT (year_month) DO UPDATE SET
            last_sequence = GREATEST(
                contract_number_counters.last_sequence,
                EXCLUDED.last_sequence
            ),
            updated_at = NOW();
    """)


def downgrade() -> None:
    op.drop_index('ix_contract_number_counters_year_month', table_name='contract_number_counters')
    op.drop_table('contract_number_counters')
