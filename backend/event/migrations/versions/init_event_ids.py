from alembic import op
import sqlalchemy as sa

revision = "init_event_ids"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "ids",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("is_occupied", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(op.f('ix_id'), 'ids', ['id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_id'), table_name='ids')
    op.drop_table("ids")
