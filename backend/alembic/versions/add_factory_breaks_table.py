"""Add factory_breaks table for multiple break times per factory

Revision ID: 006_add_factory_breaks
Revises: 295f2319d69d
Create Date: 2024-12-05

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_add_factory_breaks'
down_revision = 'a13b0ee61914'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create factory_breaks table
    op.create_table(
        'factory_breaks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('factory_id', sa.Integer(), nullable=False),
        sa.Column('break_name', sa.String(100), nullable=False),  # e.g., "昼勤", "夜勤", "残業時"
        sa.Column('break_start', sa.Time(), nullable=True),
        sa.Column('break_end', sa.Time(), nullable=True),
        sa.Column('break_minutes', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),  # Free text description
        sa.Column('display_order', sa.Integer(), nullable=True, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['factory_id'], ['factories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_factory_breaks_factory_id', 'factory_breaks', ['factory_id'])
    op.create_index('ix_factory_breaks_id', 'factory_breaks', ['id'])


def downgrade() -> None:
    op.drop_index('ix_factory_breaks_id', table_name='factory_breaks')
    op.drop_index('ix_factory_breaks_factory_id', table_name='factory_breaks')
    op.drop_table('factory_breaks')
