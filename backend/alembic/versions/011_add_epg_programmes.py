"""Add epg_programmes table for TV schedule / on-now data

Revision ID: 011
Revises: 010
Create Date: 2026-07-21
"""
from alembic import op


revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS epg_programmes (
            id SERIAL PRIMARY KEY,
            channel_id VARCHAR NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
            start_at TIMESTAMPTZ NOT NULL,
            stop_at TIMESTAMPTZ NOT NULL,
            title VARCHAR(500) NOT NULL DEFAULT '',
            subtitle VARCHAR(500) DEFAULT '',
            description TEXT DEFAULT '',
            category VARCHAR(255) DEFAULT ''
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_epg_programmes_channel_id ON epg_programmes (channel_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_epg_programmes_start_at ON epg_programmes (start_at);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_epg_programmes_stop_at ON epg_programmes (stop_at);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_epg_channel_start ON epg_programmes (channel_id, start_at);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_epg_start_stop ON epg_programmes (start_at, stop_at);")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_epg_channel_window ON epg_programmes (channel_id, start_at, stop_at);"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS epg_programmes;")
