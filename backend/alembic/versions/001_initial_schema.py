"""Initial schema with all existing tables and migrations

Revision ID: 001
Revises: 
Create Date: 2026-04-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pg_trgm extension for full-text search
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm;')
    
    # Create tables (these are handled by Base.metadata.create_all in main.py)
    # We'll add the additional columns and indexes that were in _MIGRATIONS
    
    # Add columns that might be missing (IF NOT EXISTS)
    op.execute('ALTER TABLE channels ADD COLUMN IF NOT EXISTS last_validated_at VARCHAR(50) DEFAULT \'\';')
    op.execute('ALTER TABLE radio_stations ADD COLUMN IF NOT EXISTS health_status VARCHAR(20) DEFAULT \'unknown\';')
    op.execute('ALTER TABLE radio_stations ADD COLUMN IF NOT EXISTS health_checked_at VARCHAR(50) DEFAULT \'\';')
    
    # Create indexes
    op.execute('CREATE INDEX IF NOT EXISTS ix_channels_health_status ON channels (health_status);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_channels_health_checked_at ON channels (health_checked_at);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_radio_health_status ON radio_stations (health_status);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_radio_last_check_ok ON radio_stations (last_check_ok);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_radio_health_checked_at ON radio_stations (health_checked_at);')
    
    # Create user_votes table if not exists
    op.execute('''
        CREATE TABLE IF NOT EXISTS user_votes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            item_type VARCHAR(10) NOT NULL,
            item_id VARCHAR(255) NOT NULL,
            vote_type VARCHAR(20) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    ''')
    op.execute('CREATE UNIQUE INDEX IF NOT EXISTS ix_user_vote_unique ON user_votes (user_id, item_type, item_id, vote_type);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_vote_item ON user_votes (item_type, item_id);')
    
    # Create GIN indexes for full-text search with pg_trgm
    op.execute('CREATE INDEX IF NOT EXISTS ix_channels_name_gin_trgm ON channels USING gin (name gin_trgm_ops);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_channels_alt_names_gin_trgm ON channels USING gin (alt_names gin_trgm_ops);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_channels_network_gin_trgm ON channels USING gin (network gin_trgm_ops);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_radio_name_gin_trgm ON radio_stations USING gin (name gin_trgm_ops);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_radio_tags_gin_trgm ON radio_stations USING gin (tags gin_trgm_ops);')


def downgrade() -> None:
    # Drop GIN indexes
    op.execute('DROP INDEX IF EXISTS ix_radio_tags_gin_trgm;')
    op.execute('DROP INDEX IF EXISTS ix_radio_name_gin_trgm;')
    op.execute('DROP INDEX IF EXISTS ix_channels_network_gin_trgm;')
    op.execute('DROP INDEX IF EXISTS ix_channels_alt_names_gin_trgm;')
    op.execute('DROP INDEX IF EXISTS ix_channels_name_gin_trgm;')
    
    # Drop user_votes indexes and table
    op.execute('DROP INDEX IF EXISTS ix_vote_item;')
    op.execute('DROP INDEX IF EXISTS ix_user_vote_unique;')
    op.execute('DROP TABLE IF EXISTS user_votes;')
    
    # Drop other indexes
    op.execute('DROP INDEX IF EXISTS ix_radio_health_checked_at;')
    op.execute('DROP INDEX IF EXISTS ix_radio_last_check_ok;')
    op.execute('DROP INDEX IF EXISTS ix_radio_health_status;')
    op.execute('DROP INDEX IF EXISTS ix_channels_health_checked_at;')
    op.execute('DROP INDEX IF EXISTS ix_channels_health_status;')
    
    # Drop columns (note: can't use IF EXISTS with DROP COLUMN in older PostgreSQL)
    # op.execute('ALTER TABLE radio_stations DROP COLUMN IF EXISTS health_checked_at;')
    # op.execute('ALTER TABLE radio_stations DROP COLUMN IF EXISTS health_status;')
    # op.execute('ALTER TABLE channels DROP COLUMN IF EXISTS last_validated_at;')
    
    # Drop pg_trgm extension
    op.execute('DROP EXTENSION IF EXISTS pg_trgm;')
