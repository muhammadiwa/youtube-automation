"""Create support tickets, announcements, and communication models.

Revision ID: 035
Revises: 034
Create Date: 2024-12-12

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5 - Support & Communication
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '035'
down_revision = '034'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create support and communication tables."""
    
    # Create support_tickets table
    op.create_table(
        'support_tickets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Ticket details
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        # Status and priority
        sa.Column('status', sa.String(20), nullable=False, default='open'),
        sa.Column('priority', sa.String(20), nullable=False, default='medium'),
        # Assignment
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        # Foreign keys
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_to'], ['admins.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for support_tickets
    op.create_index('ix_support_tickets_user_id', 'support_tickets', ['user_id'])
    op.create_index('ix_support_tickets_status', 'support_tickets', ['status'])
    op.create_index('ix_support_tickets_priority', 'support_tickets', ['priority'])
    op.create_index('ix_support_tickets_assigned_to', 'support_tickets', ['assigned_to'])

    # Create ticket_messages table
    op.create_table(
        'ticket_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('ticket_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Sender information
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_type', sa.String(20), nullable=False),
        # Message content
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('attachments', postgresql.JSON(), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        # Foreign keys
        sa.ForeignKeyConstraint(['ticket_id'], ['support_tickets.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for ticket_messages
    op.create_index('ix_ticket_messages_ticket_id', 'ticket_messages', ['ticket_id'])
    
    # Create broadcast_messages table
    op.create_table(
        'broadcast_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        # Message content
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_html', sa.Text(), nullable=True),
        # Targeting
        sa.Column('target_type', sa.String(20), nullable=False, default='all'),
        sa.Column('target_plans', postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column('target_statuses', postgresql.ARRAY(sa.String(50)), nullable=True),
        # Scheduling
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        # Status tracking
        sa.Column('status', sa.String(20), nullable=False, default='draft'),
        sa.Column('sent_count', sa.Integer(), nullable=False, default=0),
        sa.Column('failed_count', sa.Integer(), nullable=False, default=0),
        # Admin who created
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        # Foreign keys
        sa.ForeignKeyConstraint(['created_by'], ['admins.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for broadcast_messages
    op.create_index('ix_broadcast_messages_status', 'broadcast_messages', ['status'])
    
    # Create announcements table
    op.create_table(
        'announcements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        # Announcement content
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        # Display settings
        sa.Column('announcement_type', sa.String(20), nullable=False, default='info'),
        sa.Column('is_dismissible', sa.Boolean(), nullable=False, default=True),
        # Targeting
        sa.Column('target_plans', postgresql.ARRAY(sa.String(50)), nullable=True),
        # Scheduling
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        # Admin who created
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        # Foreign keys
        sa.ForeignKeyConstraint(['created_by'], ['admins.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for announcements
    op.create_index('ix_announcements_is_active', 'announcements', ['is_active'])
    op.create_index('ix_announcements_start_date', 'announcements', ['start_date'])
    
    # Create user_communications table
    op.create_table(
        'user_communications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Communication type
        sa.Column('communication_type', sa.String(50), nullable=False),
        # Reference to related entity
        sa.Column('reference_type', sa.String(50), nullable=True),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        # Communication details
        sa.Column('subject', sa.String(255), nullable=True),
        sa.Column('content_preview', sa.String(500), nullable=True),
        # Direction
        sa.Column('direction', sa.String(20), nullable=False, default='outbound'),
        # Status
        sa.Column('status', sa.String(20), nullable=False, default='sent'),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        # Foreign keys
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for user_communications
    op.create_index('ix_user_communications_user_id', 'user_communications', ['user_id'])
    op.create_index('ix_user_communications_communication_type', 'user_communications', ['communication_type'])


def downgrade() -> None:
    """Drop support and communication tables."""
    # Drop user_communications
    op.drop_index('ix_user_communications_communication_type', table_name='user_communications')
    op.drop_index('ix_user_communications_user_id', table_name='user_communications')
    op.drop_table('user_communications')
    
    # Drop announcements
    op.drop_index('ix_announcements_start_date', table_name='announcements')
    op.drop_index('ix_announcements_is_active', table_name='announcements')
    op.drop_table('announcements')
    
    # Drop broadcast_messages
    op.drop_index('ix_broadcast_messages_status', table_name='broadcast_messages')
    op.drop_table('broadcast_messages')
    
    # Drop ticket_messages
    op.drop_index('ix_ticket_messages_ticket_id', table_name='ticket_messages')
    op.drop_table('ticket_messages')
    
    # Drop support_tickets
    op.drop_index('ix_support_tickets_assigned_to', table_name='support_tickets')
    op.drop_index('ix_support_tickets_priority', table_name='support_tickets')
    op.drop_index('ix_support_tickets_status', table_name='support_tickets')
    op.drop_index('ix_support_tickets_user_id', table_name='support_tickets')
    op.drop_table('support_tickets')
