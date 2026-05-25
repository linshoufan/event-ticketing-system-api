"""add ticket tables

Revision ID: b1f2d3c4e5a6
Revises: 07cd7ed1625a
Create Date: 2026-05-25 11:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b1f2d3c4e5a6"
down_revision: Union[str, Sequence[str], None] = "07cd7ed1625a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("event_id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("location", sa.String(255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("checkin_radius_meters", sa.Integer(), nullable=False),
        sa.Column("event_start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "tickets",
        sa.Column("ticket_id", sa.String(36), primary_key=True),
        sa.Column("event_id", sa.String(36), sa.ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("username", sa.String(100), nullable=True),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("event_id", "user_id", name="uq_ticket_event_user"),
    )
    op.create_index("ix_tickets_user_id", "tickets", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_tickets_user_id", table_name="tickets")
    op.drop_table("tickets")
    op.drop_table("events")
