"""Add playlists tables

Revision ID: 003
Revises: 002
Create Date: 2026-04-03 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create playlists table
    op.execute('''
        CREATE TABLE IF NOT EXISTS playlists (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            description TEXT DEFAULT '',
            is_public BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        );
    ''')
    
    # Create playlist_items table
    op.execute('''
        CREATE TABLE IF NOT EXISTS playlist_items (
            id SERIAL PRIMARY KEY,
            playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
            item_type VARCHAR(10) NOT NULL,
            item_id VARCHAR(255) NOT NULL,
            item_data TEXT DEFAULT '{}',
            position INTEGER DEFAULT 0,
            added_at TIMESTAMPTZ DEFAULT now()
        );
    ''')
    
    # Create indexes
    op.execute('CREATE INDEX IF NOT EXISTS ix_playlists_user_id ON playlists (user_id);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_playlists_is_public ON playlists (is_public);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_playlist_items_playlist_id ON playlist_items (playlist_id);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_playlist_items_playlist_position ON playlist_items (playlist_id, position);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_playlist_items_item ON playlist_items (item_type, item_id);')


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS ix_playlist_items_item;')
    op.execute('DROP INDEX IF EXISTS ix_playlist_items_playlist_position;')
    op.execute('DROP INDEX IF EXISTS ix_playlist_items_playlist_id;')
    op.execute('DROP INDEX IF EXISTS ix_playlists_is_public;')
    op.execute('DROP INDEX IF EXISTS ix_playlists_user_id;')
    op.execute('DROP TABLE IF EXISTS playlist_items;')
    op.execute('DROP TABLE IF EXISTS playlists;')
