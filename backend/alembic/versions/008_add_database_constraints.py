"""Add CHECK constraints for data validation

Revision ID: 008
Revises: 007
Create Date: 2026-04-03 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add CHECK constraint for subscription_tier enum values
    op.execute('''
        ALTER TABLE users
        ADD CONSTRAINT check_subscription_tier 
        CHECK (subscription_tier IN ('free', 'plus', 'pro', 'family'));
    ''')
    
    # Add CHECK constraint for subscription_status values
    op.execute('''
        ALTER TABLE users
        ADD CONSTRAINT check_subscription_status 
        CHECK (subscription_status IN ('', 'active', 'canceled', 'past_due', 'trialing', 'incomplete', 'incomplete_expired', 'unpaid'));
    ''')
    
    # Add CHECK constraint for parental PIN length (4-6 digits)
    # Note: parental_pin_hash is bcrypt hash, so we can't validate PIN format after hashing
    # But we validate in the API layer before hashing
    
    # Add CHECK constraint for health_status values on channels
    op.execute('''
        ALTER TABLE channels
        ADD CONSTRAINT check_health_status 
        CHECK (health_status IN ('unknown', 'verified', 'online', 'offline', 'timeout', 'error'));
    ''')
    
    # Add CHECK constraint for health_status values on radio_stations
    op.execute('''
        ALTER TABLE radio_stations
        ADD CONSTRAINT check_radio_health_status 
        CHECK (health_status IN ('unknown', 'verified', 'online', 'offline', 'timeout', 'error'));
    ''')
    
    # Add CHECK constraint for item_type in user_favorites
    op.execute('''
        ALTER TABLE user_favorites
        ADD CONSTRAINT check_favorite_item_type 
        CHECK (item_type IN ('tv', 'radio'));
    ''')
    
    # Add CHECK constraint for item_type in user_votes
    op.execute('''
        ALTER TABLE user_votes
        ADD CONSTRAINT check_vote_item_type 
        CHECK (item_type IN ('tv', 'radio'));
    ''')
    
    # Add CHECK constraint for vote_type values
    op.execute('''
        ALTER TABLE user_votes
        ADD CONSTRAINT check_vote_type 
        CHECK (vote_type IN ('like', 'dislike', 'works', 'broken', 'slow', 'bad_quality'));
    ''')
    
    # Add CHECK constraint for item_type in watch_history
    op.execute('''
        ALTER TABLE watch_history
        ADD CONSTRAINT check_history_item_type 
        CHECK (item_type IN ('tv', 'radio'));
    ''')
    
    # Add CHECK constraint for playlist_items
    op.execute('''
        ALTER TABLE playlist_items
        ADD CONSTRAINT check_playlist_item_type 
        CHECK (item_type IN ('tv', 'radio'));
    ''')
    
    # Add CHECK constraint for non-negative duration
    op.execute('''
        ALTER TABLE watch_history
        ADD CONSTRAINT check_duration_seconds 
        CHECK (duration_seconds >= 0);
    ''')
    
    # Add CHECK constraint for provider in users (google, apple, passkey)
    op.execute('''
        ALTER TABLE users
        ADD CONSTRAINT check_provider 
        CHECK (provider IN ('google', 'apple', 'passkey'));
    ''')


def downgrade() -> None:
    # Remove all CHECK constraints
    op.execute('ALTER TABLE users DROP CONSTRAINT IF EXISTS check_subscription_tier;')
    op.execute('ALTER TABLE users DROP CONSTRAINT IF EXISTS check_subscription_status;')
    op.execute('ALTER TABLE users DROP CONSTRAINT IF EXISTS check_provider;')
    op.execute('ALTER TABLE channels DROP CONSTRAINT IF EXISTS check_health_status;')
    op.execute('ALTER TABLE radio_stations DROP CONSTRAINT IF EXISTS check_radio_health_status;')
    op.execute('ALTER TABLE user_favorites DROP CONSTRAINT IF EXISTS check_favorite_item_type;')
    op.execute('ALTER TABLE user_votes DROP CONSTRAINT IF EXISTS check_vote_item_type;')
    op.execute('ALTER TABLE user_votes DROP CONSTRAINT IF EXISTS check_vote_type;')
    op.execute('ALTER TABLE watch_history DROP CONSTRAINT IF EXISTS check_history_item_type;')
    op.execute('ALTER TABLE watch_history DROP CONSTRAINT IF EXISTS check_duration_seconds;')
    op.execute('ALTER TABLE playlist_items DROP CONSTRAINT IF EXISTS check_playlist_item_type;')
