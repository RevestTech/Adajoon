"""Add epg_programmes table for XMLTV ingest

Revision ID: 011
Revises: 010
Create Date: 2026-07-20

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
            channel_id VARCHAR NOT NULL,
            start_at TIMESTAMPTZ NOT NULL,
            stop_at TIMESTAMPTZ NOT NULL,
            title VARCHAR(500) NOT NULL DEFAULT '',
            subtitle VARCHAR(500) DEFAULT '',
            description TEXT DEFAULT '',
            category VARCHAR(255) DEFAULT '',
            CONSTRAINT uq_epg_channel_start UNIQUE (channel_id, start_at)
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_epg_programmes_channel_id "
        "ON epg_programmes (channel_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_epg_programmes_channel_start "
        "ON epg_programmes (channel_id, start_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_epg_programmes_start_stop "
        "ON epg_programmes (start_at, stop_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_epg_programmes_start_stop")
    op.execute("DROP INDEX IF EXISTS ix_epg_programmes_channel_start")
    op.execute("DROP INDEX IF EXISTS ix_epg_programmes_channel_id")
    op.execute("DROP TABLE IF EXISTS epg_programmes")
