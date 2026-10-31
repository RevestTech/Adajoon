"""Ensure analytics_events.properties is JSONB, matching models.py

Migration 010 always created this column as JSONB, but models.py
declared it as the generic JSON type - which on a database bootstrapped
via Base.metadata.create_all() (rather than this migration history)
produces a plain `json` column. `jsonb_extract_path_text()`, used by
every admin analytics endpoint, only accepts `jsonb`, so a create_all()'d
database 500s on all of them. Harmless no-op on a database that already
has it as JSONB (e.g. production, which ran this migration history).

Revision ID: 017
Revises: 016
Create Date: 2026-10-31

"""

from alembic import op

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE analytics_events
        ALTER COLUMN properties TYPE JSONB
        USING properties::jsonb
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE analytics_events
        ALTER COLUMN properties TYPE JSON
        USING properties::json
    """)
