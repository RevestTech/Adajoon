"""Add parental controls to users table

Revision ID: 004
Revises: 003
Create Date: 2026-04-03 04:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add parental control columns to users table
    op.execute('''
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS kids_mode_enabled BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS parental_pin_hash VARCHAR(255) DEFAULT '';
    ''')


def downgrade() -> None:
    op.execute('''
        ALTER TABLE users 
        DROP COLUMN IF EXISTS parental_pin_hash,
        DROP COLUMN IF EXISTS kids_mode_enabled;
    ''')
