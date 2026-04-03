"""Add watch history table

Revision ID: 002
Revises: 001
Create Date: 2026-04-03 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create watch_history table
    op.execute('''
        CREATE TABLE IF NOT EXISTS watch_history (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            item_type VARCHAR(10) NOT NULL,
            item_id VARCHAR(255) NOT NULL,
            item_name VARCHAR(512) NOT NULL,
            item_logo TEXT DEFAULT '',
            watched_at TIMESTAMPTZ DEFAULT now(),
            duration_seconds INTEGER DEFAULT 0
        );
    ''')
    
    # Create indexes
    op.execute('CREATE INDEX IF NOT EXISTS ix_watch_history_user_type ON watch_history (user_id, item_type, watched_at);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_watch_history_item ON watch_history (item_type, item_id);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_watch_history_watched_at ON watch_history (watched_at);')


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS ix_watch_history_watched_at;')
    op.execute('DROP INDEX IF EXISTS ix_watch_history_item;')
    op.execute('DROP INDEX IF EXISTS ix_watch_history_user_type;')
    op.execute('DROP TABLE IF EXISTS watch_history;')
