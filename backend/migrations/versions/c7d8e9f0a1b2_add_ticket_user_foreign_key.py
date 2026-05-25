"""add ticket user foreign key

Revision ID: c7d8e9f0a1b2
Revises: b1f2d3c4e5a6
Create Date: 2026-05-25 12:10:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "b1f2d3c4e5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_tickets_user_id_users",
        "tickets",
        "users",
        ["user_id"],
        ["user_id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_tickets_user_id_users", "tickets", type_="foreignkey")
