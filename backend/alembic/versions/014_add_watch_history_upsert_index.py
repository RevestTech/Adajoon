"""Add the unique index watch history upserts rely on but migration 002 never created

Revision ID: 014
Revises: 013
Create Date: 2026-10-25

history.py's POST /api/history/record has always upserted via
`on_conflict_do_update(constraint="ix_watch_history_user_item_recent")`,
but no migration ever created that index - every call fell through to
the except block and 500'd. A sliding "last 1 hour" partial unique index
(as history.py's comment describes) isn't valid Postgres anyway (a
partial index predicate can't depend on now()), so this is a plain
unique index on (user_id, item_type, item_id): one history row per
item per user, continuously bumped - which matches what GET
/api/history/ already assumes (a flat watched_at-ordered list, no
per-item grouping).
"""

from alembic import op

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Collapse any existing duplicates to their most recently watched row
    # first, or the unique index below would fail to create.
    op.execute("""
        DELETE FROM watch_history wh
        WHERE wh.id NOT IN (
            SELECT DISTINCT ON (user_id, item_type, item_id) id
            FROM watch_history
            ORDER BY user_id, item_type, item_id, watched_at DESC
        );
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_watch_history_user_item_recent
        ON watch_history (user_id, item_type, item_id);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_watch_history_user_item_recent;")
