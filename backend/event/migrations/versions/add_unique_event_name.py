"""align event columns and constraints

Revision ID: add_unique_event_name
Revises: init_events
Create Date: 2026-06-02 12:00:00.000000

"""
from alembic import op


revision = "add_unique_event_name"
down_revision = "init_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'events'
                  AND column_name = 'checkinRadiusMeters'
            ) AND NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'events'
                  AND column_name = 'checkin_radius_meters'
            ) THEN
                ALTER TABLE events RENAME COLUMN "checkinRadiusMeters" TO checkin_radius_meters;
            ELSIF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'events'
                  AND column_name = 'checkinRadiusMeters'
            ) AND EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'events'
                  AND column_name = 'checkin_radius_meters'
            ) THEN
                UPDATE events
                SET checkin_radius_meters = COALESCE(checkin_radius_meters, "checkinRadiusMeters");
                ALTER TABLE events DROP COLUMN "checkinRadiusMeters";
            END IF;

            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_events_name'
            ) THEN
                ALTER TABLE events ADD CONSTRAINT uq_events_name UNIQUE (name);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_events_name'
            ) THEN
                ALTER TABLE events DROP CONSTRAINT uq_events_name;
            END IF;

            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'events'
                  AND column_name = 'checkin_radius_meters'
            ) AND NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'events'
                  AND column_name = 'checkinRadiusMeters'
            ) THEN
                ALTER TABLE events RENAME COLUMN checkin_radius_meters TO "checkinRadiusMeters";
            END IF;
        END $$;
        """
    )
