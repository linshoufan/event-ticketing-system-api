from alembic import op

revision = "event_category_check"
down_revision = "add_unique_event_name"   # 目前的 head
branch_labels = None
depends_on = None

def upgrade():
    op.create_check_constraint(
        "check_event_category", "events",
        "category IS NULL OR category IN "
        "('sport','food','travel','culture','family','contest','music')")

def downgrade():
    op.drop_constraint("check_event_category", "events", type_="check")