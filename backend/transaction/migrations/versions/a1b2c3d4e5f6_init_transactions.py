"""init transactions table

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-05-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "transactions",
        sa.Column("transaction_id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("event_id", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="confirmed"),
        sa.Column("waitlist_number", sa.Integer(), nullable=True),
        sa.Column("guest_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("diet_type", sa.String(10), nullable=True),
        sa.Column("self_driving", sa.Boolean(), nullable=True),
        sa.Column("ticket_id", sa.String(36), nullable=True),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('confirmed','waitlist','cancelled')",
            name="check_transaction_status",
        ),
        sa.CheckConstraint(
            "diet_type IN ('veg','non-veg','none')",
            name="check_transaction_diet_type",
        ),
        sa.CheckConstraint(
            "guest_count >= 0",
            name="check_transaction_guest_count_non_negative",
        ),
    )

    # 一般索引
    op.create_index(
        "ix_transactions_event_status",
        "transactions",
        ["event_id", "status"],
    )
    op.create_index(
        "ix_transactions_user_id",
        "transactions",
        ["user_id"],
    )

    # ⚠️ Partial unique index：同一個 user 對同一個 event 不能有 2 筆 active 紀錄
    # 但允許重複報名再取消再報（cancelled 不在範圍內）
    op.create_index(
        "uq_active_registration",
        "transactions",
        ["user_id", "event_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('confirmed','waitlist')"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_active_registration", table_name="transactions")
    op.drop_index("ix_transactions_user_id", table_name="transactions")
    op.drop_index("ix_transactions_event_status", table_name="transactions")
    op.drop_table("transactions")