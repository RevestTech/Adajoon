"""Add app_settings table and admin_hidden on channels/radio_stations

app_settings is a small shared key/value store for simple admin on/off
switches (starting with the ads kill switch) rather than a bespoke
column/table per toggle.

admin_hidden lets an admin permanently hide a channel/station from the
public catalog, independent of is_active/last_check_ok - both of which
the external sync jobs overwrite on every run.

Revision ID: 018
Revises: 017
Create Date: 2026-10-31

"""

from alembic import op

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key VARCHAR(100) PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute(
        "ALTER TABLE channels ADD COLUMN IF NOT EXISTS admin_hidden BOOLEAN DEFAULT FALSE"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_channels_admin_hidden ON channels (admin_hidden)"
    )
    op.execute("UPDATE channels SET admin_hidden = FALSE WHERE admin_hidden IS NULL")

    op.execute(
        "ALTER TABLE radio_stations ADD COLUMN IF NOT EXISTS admin_hidden BOOLEAN DEFAULT FALSE"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_radio_admin_hidden ON radio_stations (admin_hidden)"
    )
    op.execute(
        "UPDATE radio_stations SET admin_hidden = FALSE WHERE admin_hidden IS NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_radio_admin_hidden")
    op.execute("ALTER TABLE radio_stations DROP COLUMN IF EXISTS admin_hidden")
    op.execute("DROP INDEX IF EXISTS ix_channels_admin_hidden")
    op.execute("ALTER TABLE channels DROP COLUMN IF EXISTS admin_hidden")
    op.execute("DROP TABLE IF EXISTS app_settings")
