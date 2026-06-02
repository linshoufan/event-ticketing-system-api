"""init users tables

Revision ID: 07cd7ed1625a
Revises:
Create Date: 2026-05-20 17:01:24.819449

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07cd7ed1625a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="employee"),
        sa.Column("registration_status", sa.String(10), nullable=False, server_default="active"),
        sa.Column("unlock_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("diet_type", sa.String(10), nullable=True, server_default="non-veg"),
        sa.Column("self_driving", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('employee','welfare_member','hr')", name="check_user_role"),
        sa.CheckConstraint("registration_status IN ('active','locked')", name="check_registration_status"),
        sa.CheckConstraint("diet_type IN ('veg','non-veg')", name="check_diet_type"),
    )
    op.create_table(
        "user_interest_tags",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("tag", sa.String(50), nullable=False),
        sa.UniqueConstraint("user_id", "tag"),
        sa.CheckConstraint(
            "tag IN ('sport','food','travel','culture','family','contest','music')",
            name="check_tag",
        ),
    )
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("diet_type", sa.String(10), nullable=True),
        sa.Column("self_driving", sa.Boolean(), nullable=True),
        sa.Column("guest_count", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "category"),
        sa.CheckConstraint("diet_type IN ('veg','non-veg')", name="check_preference_diet_type"),
        sa.CheckConstraint(
            "category IN ('sport','food','travel','culture','family','contest','music')",
            name="check_preference_category",
        ),
    )


def downgrade() -> None:
    op.drop_table("user_preferences")
    op.drop_table("user_interest_tags")
    op.drop_table("users")
