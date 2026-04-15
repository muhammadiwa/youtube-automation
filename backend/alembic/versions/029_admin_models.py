"""Create admin table for admin panel.

Revision ID: 029
Revises: 028
Create Date: 2024-12-12

Requirements: 1.1, 1.4 - Admin Authentication & Authorization
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '029'
down_revision = '028'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create admins table."""
    op.create_table(
        'admins',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('role', sa.String(50), nullable=False, default='admin'),
        sa.Column('permissions', postgresql.ARRAY(sa.String(100)), nullable=False, default=[]),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    
    # Create index on user_id for faster lookups
    op.create_index('ix_admins_user_id', 'admins', ['user_id'])
    
    # Create index on role for filtering
    op.create_index('ix_admins_role', 'admins', ['role'])
    
    # Create index on is_active for filtering active admins
    op.create_index('ix_admins_is_active', 'admins', ['is_active'])
    
    # Seed the default admin user as super_admin
    # This assumes the admin user was created in migration 027
    admins_table = sa.table(
        'admins',
        sa.column('id', postgresql.UUID),
        sa.column('user_id', postgresql.UUID),
        sa.column('role', sa.String),
        sa.column('permissions', postgresql.ARRAY(sa.String)),
        sa.column('is_active', sa.Boolean),
    )
    
    # Get the admin user ID from users table
    # We'll use a raw SQL to get the user ID and insert the admin record
    op.execute("""
        INSERT INTO admins (id, user_id, role, permissions, is_active)
        SELECT 
            gen_random_uuid(),
            id,
            'super_admin',
            ARRAY[
                'view_users', 'manage_users', 'impersonate_users',
                'view_billing', 'manage_billing', 'process_refunds',
                'view_system', 'manage_system', 'manage_config',
                'view_moderation', 'manage_moderation',
                'view_analytics', 'export_data',
                'view_audit_logs', 'manage_compliance',
                'manage_admins'
            ],
            true
        FROM users
        WHERE email = 'admin@youtubeautomation.com'
        ON CONFLICT (user_id) DO NOTHING
    """)


def downgrade() -> None:
    """Drop admins table."""
    op.drop_index('ix_admins_is_active', table_name='admins')
    op.drop_index('ix_admins_role', table_name='admins')
    op.drop_index('ix_admins_user_id', table_name='admins')
    op.drop_table('admins')
