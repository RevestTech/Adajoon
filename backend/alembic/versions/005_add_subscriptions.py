"""Add subscription fields to users table

Revision ID: 005
Revises: 004
Create Date: 2026-04-03 05:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add subscription columns to users table
    op.execute('''
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255) DEFAULT '',
        ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(50) DEFAULT 'free',
        ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50) DEFAULT '',
        ADD COLUMN IF NOT EXISTS subscription_ends_at TIMESTAMPTZ DEFAULT NULL;
    ''')
    
    # Create indexes
    op.execute('CREATE INDEX IF NOT EXISTS ix_users_stripe_customer_id ON users (stripe_customer_id);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_users_subscription_tier ON users (subscription_tier);')


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS ix_users_subscription_tier;')
    op.execute('DROP INDEX IF EXISTS ix_users_stripe_customer_id;')
    op.execute('''
        ALTER TABLE users 
        DROP COLUMN IF EXISTS subscription_ends_at,
        DROP COLUMN IF EXISTS subscription_status,
        DROP COLUMN IF EXISTS subscription_tier,
        DROP COLUMN IF EXISTS stripe_customer_id;
    ''')
