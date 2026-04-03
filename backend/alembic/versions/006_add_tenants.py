"""Add tenants table for white-label B2B

Revision ID: 006
Revises: 005
Create Date: 2026-04-03 06:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tenants table
    op.execute('''
        CREATE TABLE IF NOT EXISTS tenants (
            id SERIAL PRIMARY KEY,
            slug VARCHAR(100) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            custom_domain VARCHAR(255) DEFAULT '',
            logo_url TEXT DEFAULT '',
            primary_color VARCHAR(7) DEFAULT '#667eea',
            secondary_color VARCHAR(7) DEFAULT '#764ba2',
            api_key VARCHAR(255) NOT NULL UNIQUE,
            allowed_origins TEXT DEFAULT '',
            max_channels INTEGER DEFAULT 1000,
            max_requests_per_day INTEGER DEFAULT 100000,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    ''')
    
    # Create indexes
    op.execute('CREATE INDEX IF NOT EXISTS ix_tenants_slug ON tenants (slug);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_tenants_api_key ON tenants (api_key);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_tenants_is_active ON tenants (is_active);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_tenants_active_slug ON tenants (is_active, slug);')


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS ix_tenants_active_slug;')
    op.execute('DROP INDEX IF EXISTS ix_tenants_is_active;')
    op.execute('DROP INDEX IF EXISTS ix_tenants_api_key;')
    op.execute('DROP INDEX IF EXISTS ix_tenants_slug;')
    op.execute('DROP TABLE IF EXISTS tenants;')
