"""Add movies table

Adajoon hosts no video itself for movies - stream_url points at a
syndication partner's (or other licensed source's) already-hosted
stream, the same model as channels.stream_url.

Revision ID: 016
Revises: 015
Create Date: 2026-10-30

"""

from alembic import op

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id SERIAL PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            synopsis TEXT DEFAULT '',
            poster_url TEXT DEFAULT '',
            year INTEGER,
            duration_minutes INTEGER,
            genres VARCHAR(500) DEFAULT '',
            source VARCHAR(255) DEFAULT '',
            stream_url TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_movies_title ON movies (title)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_movies_is_active ON movies (is_active)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS movies")
