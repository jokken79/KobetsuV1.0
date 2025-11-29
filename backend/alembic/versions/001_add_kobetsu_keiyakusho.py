"""add kobetsu_keiyakusho table

Revision ID: add_kobetsu_keiyakusho
Revises: (previous revision)
Create Date: 2024-11-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_kobetsu_keiyakusho'
down_revision = '000_create_base_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create kobetsu_keiyakusho table
    op.create_table(
        'kobetsu_keiyakusho',
        sa.Column('id', sa.Integer(), nullable=False),
        
        # Relaciones
        sa.Column('factory_id', sa.Integer(), nullable=False),
        sa.Column('dispatch_assignment_id', sa.Integer(), nullable=True),
        
        # 基本情報
        sa.Column('contract_number', sa.String(50), nullable=False),
        sa.Column('contract_date', sa.Date(), nullable=False),
        sa.Column('dispatch_start_date', sa.Date(), nullable=False),
        sa.Column('dispatch_end_date', sa.Date(), nullable=False),
        
        # 業務内容 (Items 1-2)
        sa.Column('work_content', sa.Text(), nullable=False),
        sa.Column('responsibility_level', sa.String(50), nullable=False),
        
        # 派遣先情報 (Item 3)
        sa.Column('worksite_name', sa.String(255), nullable=False),
        sa.Column('worksite_address', sa.Text(), nullable=False),
        sa.Column('organizational_unit', sa.String(100), nullable=True),
        
        # 指揮命令者 (Item 4)
        sa.Column('supervisor_department', sa.String(100), nullable=False),
        sa.Column('supervisor_position', sa.String(100), nullable=False),
        sa.Column('supervisor_name', sa.String(100), nullable=False),
        
        # 就業条件 (Items 5-6)
        sa.Column('work_days', postgresql.JSONB(), nullable=False),
        sa.Column('work_start_time', sa.Time(), nullable=False),
        sa.Column('work_end_time', sa.Time(), nullable=False),
        sa.Column('break_time_minutes', sa.Integer(), nullable=False),
        
        # 時間外労働 (Item 12)
        sa.Column('overtime_max_hours_day', sa.Numeric(4, 2), nullable=True),
        sa.Column('overtime_max_hours_month', sa.Numeric(5, 2), nullable=True),
        sa.Column('overtime_max_days_month', sa.Integer(), nullable=True),
        sa.Column('holiday_work_max_days', sa.Integer(), nullable=True),
        
        # 安全衛生 (Item 7)
        sa.Column('safety_measures', sa.Text(), nullable=True),
        
        # 苦情処理 (Item 8)
        sa.Column('haken_moto_complaint_contact', postgresql.JSONB(), nullable=False),
        sa.Column('haken_saki_complaint_contact', postgresql.JSONB(), nullable=False),
        
        # 派遣料金
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=False),
        sa.Column('overtime_rate', sa.Numeric(10, 2), nullable=False),
        sa.Column('night_shift_rate', sa.Numeric(10, 2), nullable=True),
        sa.Column('holiday_rate', sa.Numeric(10, 2), nullable=True),
        
        # 福利厚生 (Item 13)
        sa.Column('welfare_facilities', postgresql.JSONB(), nullable=True),
        
        # 責任者 (Items 10-11)
        sa.Column('haken_moto_manager', postgresql.JSONB(), nullable=False),
        sa.Column('haken_saki_manager', postgresql.JSONB(), nullable=False),
        
        # 契約解除 (Item 9)
        sa.Column('termination_measures', sa.Text(), nullable=True),
        
        # その他法定事項
        sa.Column('is_kyotei_taisho', sa.Boolean(), default=False),  # Item 15
        sa.Column('is_direct_hire_prevention', sa.Boolean(), default=False),  # Item 14
        sa.Column('is_mukeiko_60over_only', sa.Boolean(), default=False),  # Item 16
        
        # 派遣人数
        sa.Column('number_of_workers', sa.Integer(), nullable=False),
        
        # Status y metadata
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('pdf_path', sa.String(500), nullable=True),
        sa.Column('signed_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('contract_number'),
        sa.ForeignKeyConstraint(['factory_id'], ['factories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dispatch_assignment_id'], ['dispatch_assignments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        
        # Indexes
        sa.Index('ix_kobetsu_factory_id', 'factory_id'),
        sa.Index('ix_kobetsu_status', 'status'),
        sa.Index('ix_kobetsu_dispatch_dates', 'dispatch_start_date', 'dispatch_end_date'),
        sa.Index('ix_kobetsu_contract_number', 'contract_number'),
    )
    
    # Create table for employees assigned to each contract
    # 重要: 同じラインでも従業員ごとに異なる単価を保存できます
    op.create_table(
        'kobetsu_employees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kobetsu_keiyakusho_id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),

        # 個別単価 (Individual Rates per Employee)
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=True),
        sa.Column('overtime_rate', sa.Numeric(10, 2), nullable=True),
        sa.Column('night_shift_rate', sa.Numeric(10, 2), nullable=True),
        sa.Column('holiday_rate', sa.Numeric(10, 2), nullable=True),
        sa.Column('billing_rate', sa.Numeric(10, 2), nullable=True),

        # 派遣期間 (Individual Dispatch Period)
        sa.Column('individual_start_date', sa.Date(), nullable=True),
        sa.Column('individual_end_date', sa.Date(), nullable=True),

        # 雇用形態
        sa.Column('is_indefinite_employment', sa.Boolean(), nullable=False, server_default='false'),

        # メタデータ
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['kobetsu_keiyakusho_id'], ['kobetsu_keiyakusho.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('kobetsu_keiyakusho_id', 'employee_id', name='uq_kobetsu_employee'),

        sa.Index('ix_kobetsu_employees_kobetsu_id', 'kobetsu_keiyakusho_id'),
        sa.Index('ix_kobetsu_employees_employee_id', 'employee_id'),
    )
    
    # Add check constraints
    op.create_check_constraint(
        'ck_kobetsu_status',
        'kobetsu_keiyakusho',
        sa.column('status').in_(['draft', 'active', 'expired', 'cancelled', 'renewed'])
    )
    
    op.create_check_constraint(
        'ck_kobetsu_dates',
        'kobetsu_keiyakusho',
        'dispatch_start_date <= dispatch_end_date'
    )
    
    op.create_check_constraint(
        'ck_kobetsu_workers',
        'kobetsu_keiyakusho',
        'number_of_workers > 0'
    )


def downgrade():
    op.drop_table('kobetsu_employees')
    op.drop_table('kobetsu_keiyakusho')
