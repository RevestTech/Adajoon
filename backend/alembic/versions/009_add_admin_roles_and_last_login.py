"""add admin roles and last login

Revision ID: 009
Revises: 008
Create Date: 2026-04-12

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add last_login_at column
    op.execute("""
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ DEFAULT NULL
    """)

    # Add is_admin column (default False)
    op.execute("""
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE NOT NULL
    """)

    # Add role column (default 'user')
    op.execute("""
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'user' NOT NULL
    """)

    # Create indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_users_is_admin ON users (is_admin)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_users_role ON users (role)
    """)


def downgrade() -> None:
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS ix_users_is_admin")
    op.execute("DROP INDEX IF EXISTS ix_users_role")

    # Drop columns
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS role")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS is_admin")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS last_login_at")
