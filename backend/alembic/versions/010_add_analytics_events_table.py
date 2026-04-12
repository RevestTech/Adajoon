"""Add analytics_events table for custom analytics tracking

Revision ID: 010
Revises: 009
Create Date: 2026-04-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS analytics_events (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            session_id VARCHAR(255) NOT NULL,
            event_name VARCHAR(100) NOT NULL,
            properties JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
        )
    """)
    
    op.execute("CREATE INDEX IF NOT EXISTS ix_analytics_events_user_id ON analytics_events (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_analytics_events_session_id ON analytics_events (session_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_analytics_events_event_name ON analytics_events (event_name)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_analytics_events_created_at ON analytics_events (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_analytics_event_name_created ON analytics_events (event_name, created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_analytics_user_created ON analytics_events (user_id, created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_analytics_session_created ON analytics_events (session_id, created_at)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_analytics_session_created")
    op.execute("DROP INDEX IF EXISTS ix_analytics_user_created")
    op.execute("DROP INDEX IF EXISTS ix_analytics_event_name_created")
    op.execute("DROP INDEX IF EXISTS ix_analytics_events_created_at")
    op.execute("DROP INDEX IF EXISTS ix_analytics_events_event_name")
    op.execute("DROP INDEX IF EXISTS ix_analytics_events_session_id")
    op.execute("DROP INDEX IF EXISTS ix_analytics_events_user_id")
    op.execute("DROP TABLE IF EXISTS analytics_events")
