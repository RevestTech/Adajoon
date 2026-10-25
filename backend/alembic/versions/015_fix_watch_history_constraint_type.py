"""Replace watch_history's unique index with an actual unique constraint

Revision ID: 015
Revises: 014
Create Date: 2026-10-25

Migration 014 created `ix_watch_history_user_item_recent` as a plain
CREATE UNIQUE INDEX, which only registers an index - not a constraint in
pg_constraint. history.py's `on_conflict_do_update(constraint=...)`
compiles to `ON CONFLICT ON CONSTRAINT`, which Postgres resolves against
pg_constraint specifically, so it kept failing with "constraint ... does
not exist" even after 014 ran. Dropping the index and adding the same
columns as a real UNIQUE constraint (which Postgres backs with an
equivalent index anyway) fixes it.
"""

from alembic import op

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_watch_history_user_item_recent;")
    op.execute("""
        ALTER TABLE watch_history
        ADD CONSTRAINT ix_watch_history_user_item_recent
        UNIQUE (user_id, item_type, item_id);
    """)


def downgrade() -> None:
    op.execute(
        "ALTER TABLE watch_history DROP CONSTRAINT IF EXISTS ix_watch_history_user_item_recent;"
    )
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_watch_history_user_item_recent
        ON watch_history (user_id, item_type, item_id);
    """)
