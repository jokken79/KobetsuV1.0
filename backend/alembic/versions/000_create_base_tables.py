"""create base tables (users, factories, employees)

Revision ID: 000_create_base_tables
Revises: None
Create Date: 2024-11-25

This migration creates the foundational tables:
- users (for authentication)
- factories (派遣先/工場)
- factory_lines (配属先/ライン)
- employees (派遣社員)
- dispatch_assignments (optional, for linking)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '000_create_base_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ========================================
    # USERS TABLE
    # ========================================
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100), nullable=True),
        sa.Column('role', sa.String(20), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # ========================================
    # FACTORIES TABLE (派遣先/工場)
    # ========================================
    op.create_table(
        'factories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('factory_id', sa.String(200), nullable=False),

        # 派遣先情報 (Client Company)
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('company_address', sa.Text(), nullable=True),
        sa.Column('company_phone', sa.String(50), nullable=True),
        sa.Column('company_fax', sa.String(50), nullable=True),

        # 派遣先責任者
        sa.Column('client_responsible_department', sa.String(100), nullable=True),
        sa.Column('client_responsible_name', sa.String(100), nullable=True),
        sa.Column('client_responsible_phone', sa.String(50), nullable=True),

        # 派遣先苦情処理担当者
        sa.Column('client_complaint_department', sa.String(100), nullable=True),
        sa.Column('client_complaint_name', sa.String(100), nullable=True),
        sa.Column('client_complaint_phone', sa.String(50), nullable=True),

        # 工場情報 (Plant)
        sa.Column('plant_name', sa.String(255), nullable=False),
        sa.Column('plant_address', sa.Text(), nullable=True),
        sa.Column('plant_phone', sa.String(50), nullable=True),

        # 派遣元情報 (Dispatch Company - UNS)
        sa.Column('dispatch_responsible_department', sa.String(100), nullable=True),
        sa.Column('dispatch_responsible_name', sa.String(100), nullable=True),
        sa.Column('dispatch_responsible_phone', sa.String(50), nullable=True),
        sa.Column('dispatch_complaint_department', sa.String(100), nullable=True),
        sa.Column('dispatch_complaint_name', sa.String(100), nullable=True),
        sa.Column('dispatch_complaint_phone', sa.String(50), nullable=True),

        # スケジュール (Schedule)
        sa.Column('work_hours_description', sa.Text(), nullable=True),
        sa.Column('break_time_description', sa.Text(), nullable=True),
        sa.Column('calendar_description', sa.Text(), nullable=True),
        sa.Column('day_shift_start', sa.Time(), nullable=True),
        sa.Column('day_shift_end', sa.Time(), nullable=True),
        sa.Column('night_shift_start', sa.Time(), nullable=True),
        sa.Column('night_shift_end', sa.Time(), nullable=True),
        sa.Column('break_minutes', sa.Integer(), nullable=False, server_default='60'),

        # 時間外労働
        sa.Column('overtime_description', sa.Text(), nullable=True),
        sa.Column('overtime_max_hours_day', sa.Numeric(4, 2), nullable=True),
        sa.Column('overtime_max_hours_month', sa.Numeric(5, 2), nullable=True),
        sa.Column('overtime_max_hours_year', sa.Integer(), nullable=True),
        sa.Column('overtime_special_max_month', sa.Numeric(5, 2), nullable=True),
        sa.Column('overtime_special_count_year', sa.Integer(), nullable=True),

        # 休日労働
        sa.Column('holiday_work_description', sa.Text(), nullable=True),
        sa.Column('holiday_work_max_days_month', sa.Integer(), nullable=True),

        # 抵触日
        sa.Column('conflict_date', sa.Date(), nullable=True),
        sa.Column('time_unit_minutes', sa.Numeric(4, 1), nullable=True, server_default='15'),

        # 支払条件 (Payment Terms)
        sa.Column('closing_date', sa.String(50), nullable=True),
        sa.Column('payment_date', sa.String(50), nullable=True),
        sa.Column('bank_account', sa.Text(), nullable=True),
        sa.Column('worker_closing_date', sa.String(50), nullable=True),
        sa.Column('worker_payment_date', sa.String(50), nullable=True),
        sa.Column('worker_calendar', sa.Text(), nullable=True),

        # 協定 (Agreement)
        sa.Column('agreement_period', sa.Date(), nullable=True),
        sa.Column('agreement_explainer', sa.String(255), nullable=True),

        # メタデータ
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('factory_id'),
    )
    op.create_index('ix_factories_factory_id', 'factories', ['factory_id'])
    op.create_index('ix_factories_company_name', 'factories', ['company_name'])
    op.create_index('ix_factories_plant_name', 'factories', ['plant_name'])
    op.create_index('ix_factories_company_plant', 'factories', ['company_name', 'plant_name'])
    op.create_index('ix_factories_conflict_date', 'factories', ['conflict_date'])

    # ========================================
    # FACTORY_LINES TABLE (配属先/ライン)
    # ========================================
    op.create_table(
        'factory_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('factory_id', sa.Integer(), nullable=False),
        sa.Column('line_id', sa.String(50), nullable=True),

        # 配属先情報
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('line_name', sa.String(100), nullable=True),

        # 指揮命令者
        sa.Column('supervisor_department', sa.String(100), nullable=True),
        sa.Column('supervisor_name', sa.String(100), nullable=True),
        sa.Column('supervisor_phone', sa.String(50), nullable=True),

        # 業務内容
        sa.Column('job_description', sa.Text(), nullable=True),
        sa.Column('job_description_detail', sa.Text(), nullable=True),
        sa.Column('responsibility_level', sa.String(50), nullable=False, server_default='通常業務'),

        # 料金
        sa.Column('hourly_rate', sa.Numeric(8, 2), nullable=True),
        sa.Column('billing_rate', sa.Numeric(8, 2), nullable=True),
        sa.Column('overtime_rate', sa.Numeric(8, 2), nullable=True),
        sa.Column('night_rate', sa.Numeric(8, 2), nullable=True),
        sa.Column('holiday_rate', sa.Numeric(8, 2), nullable=True),

        # メタデータ
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['factory_id'], ['factories.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('factory_id', 'line_id', name='uq_factory_line'),
    )
    op.create_index('ix_factory_lines_factory_id', 'factory_lines', ['factory_id'])
    op.create_index('ix_factory_lines_line_id', 'factory_lines', ['line_id'])

    # ========================================
    # EMPLOYEES TABLE (派遣社員)
    # ========================================
    op.create_table(
        'employees',
        sa.Column('id', sa.Integer(), nullable=False),

        # 識別情報
        sa.Column('employee_number', sa.String(20), nullable=False),
        sa.Column('hakenmoto_id', sa.String(50), nullable=True),
        sa.Column('rirekisho_id', sa.String(50), nullable=True),

        # 基本情報
        sa.Column('full_name_kanji', sa.String(100), nullable=False),
        sa.Column('full_name_kana', sa.String(100), nullable=False),
        sa.Column('full_name_romaji', sa.String(100), nullable=True),
        sa.Column('gender', sa.String(10), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('nationality', sa.String(50), nullable=False, server_default='ベトナム'),

        # 連絡先
        sa.Column('postal_code', sa.String(10), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('mobile', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),

        # 緊急連絡先
        sa.Column('emergency_contact_name', sa.String(100), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(20), nullable=True),
        sa.Column('emergency_contact_relationship', sa.String(50), nullable=True),

        # 雇用情報
        sa.Column('hire_date', sa.Date(), nullable=False),
        sa.Column('termination_date', sa.Date(), nullable=True),
        sa.Column('termination_reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('contract_type', sa.String(50), nullable=True),
        sa.Column('employment_type', sa.String(50), nullable=True),

        # 派遣先情報 (Current Assignment)
        sa.Column('factory_id', sa.Integer(), nullable=True),
        sa.Column('factory_line_id', sa.Integer(), nullable=True),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('plant_name', sa.String(255), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('line_name', sa.String(100), nullable=True),
        sa.Column('position', sa.String(100), nullable=True),

        # 給与情報
        sa.Column('hourly_rate', sa.Numeric(8, 2), nullable=True),
        sa.Column('billing_rate', sa.Numeric(8, 2), nullable=True),
        sa.Column('transportation_allowance', sa.Numeric(8, 2), nullable=True, server_default='0'),

        # 在留資格
        sa.Column('visa_type', sa.String(100), nullable=True),
        sa.Column('visa_status', sa.String(100), nullable=True),
        sa.Column('visa_expiry_date', sa.Date(), nullable=True),
        sa.Column('zairyu_card_number', sa.String(50), nullable=True),
        sa.Column('zairyu_card_expiry', sa.Date(), nullable=True),
        sa.Column('passport_number', sa.String(50), nullable=True),
        sa.Column('passport_expiry', sa.Date(), nullable=True),

        # 保険情報
        sa.Column('has_employment_insurance', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('employment_insurance_number', sa.String(50), nullable=True),
        sa.Column('has_health_insurance', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('health_insurance_number', sa.String(50), nullable=True),
        sa.Column('has_pension_insurance', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('pension_insurance_number', sa.String(50), nullable=True),
        sa.Column('has_workers_comp', sa.Boolean(), nullable=False, server_default='true'),

        # 有給休暇
        sa.Column('yukyu_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('yukyu_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('yukyu_remaining', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('yukyu_grant_date', sa.Date(), nullable=True),

        # 住居情報
        sa.Column('apartment_id', sa.Integer(), nullable=True),
        sa.Column('apartment_name', sa.String(255), nullable=True),
        sa.Column('apartment_room', sa.String(50), nullable=True),
        sa.Column('apartment_rent', sa.Numeric(8, 2), nullable=True),
        sa.Column('is_corporate_housing', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('housing_subsidy', sa.Numeric(8, 2), nullable=True, server_default='0'),

        # 銀行口座
        sa.Column('bank_name', sa.String(100), nullable=True),
        sa.Column('bank_branch', sa.String(100), nullable=True),
        sa.Column('bank_account_type', sa.String(20), nullable=True),
        sa.Column('bank_account_number', sa.String(20), nullable=True),
        sa.Column('bank_account_holder', sa.String(100), nullable=True),

        # 資格・免許
        sa.Column('qualifications', sa.Text(), nullable=True),
        sa.Column('drivers_license', sa.String(50), nullable=True),
        sa.Column('drivers_license_expiry', sa.Date(), nullable=True),
        sa.Column('forklift_license', sa.Boolean(), nullable=False, server_default='false'),

        # メモ
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('photo_url', sa.String(500), nullable=True),

        # タイムスタンプ
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_number'),
        sa.ForeignKeyConstraint(['factory_id'], ['factories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['factory_line_id'], ['factory_lines.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_employees_employee_number', 'employees', ['employee_number'])
    op.create_index('ix_employees_full_name_kana', 'employees', ['full_name_kana'])
    op.create_index('ix_employees_company_name', 'employees', ['company_name'])
    op.create_index('ix_employees_status', 'employees', ['status'])
    op.create_index('ix_employees_factory_id', 'employees', ['factory_id'])
    op.create_index('ix_employees_hire_date', 'employees', ['hire_date'])
    op.create_index('ix_employees_visa_expiry_date', 'employees', ['visa_expiry_date'])
    op.create_index('ix_employees_status_company', 'employees', ['status', 'company_name'])
    op.create_index('ix_employees_hakenmoto_id', 'employees', ['hakenmoto_id'])

    # ========================================
    # DISPATCH_ASSIGNMENTS TABLE (Optional)
    # ========================================
    op.create_table(
        'dispatch_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('dispatch_assignments')
    op.drop_table('employees')
    op.drop_table('factory_lines')
    op.drop_table('factories')
    op.drop_table('users')
