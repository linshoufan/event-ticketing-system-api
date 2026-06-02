"""init events

Revision ID: init_events
Revises: 
Create Date: 2026-06-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'init_events'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'events',
        sa.Column('event_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('guest_allowed', sa.Boolean(), nullable=False),
        sa.Column('ticket_limit', sa.Integer(), nullable=True),
        sa.Column('remaining_tickets', sa.Integer(), nullable=False),
        sa.Column('cancellation_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('checkin_radius_meters', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('event_start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('registration_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('registration_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('faqs', sa.JSON(), nullable=True),
        sa.Column('status', sa.Integer(), nullable=False),
        sa.Column('is_draft', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('event_id')
    )
    op.create_index(op.f('ix_events_category'), 'events', ['category'], unique=False)
    op.create_index(op.f('ix_events_event_id'), 'events', ['event_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_events_event_id'), table_name='events')
    op.drop_index(op.f('ix_events_category'), table_name='events')
    op.drop_table('events')
