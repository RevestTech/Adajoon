"""Add user_devices table

Backs real per-tier device-limit enforcement (pro/family tiers advertise
"5 devices"/"10 devices" but nothing enforced it - see
app.services.device_service). Each row is one device/browser that has
logged in as a given user.

Revision ID: 019
Revises: 018
Create Date: 2026-11-10

"""

from alembic import op

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_devices (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            device_id VARCHAR(128) NOT NULL,
            label VARCHAR(255) DEFAULT '',
            first_seen_at TIMESTAMPTZ DEFAULT now(),
            last_seen_at TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_user_device_unique "
        "ON user_devices (user_id, device_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_user_devices_user_id ON user_devices (user_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_user_devices_user_id")
    op.execute("DROP INDEX IF EXISTS ix_user_device_unique")
    op.execute("DROP TABLE IF EXISTS user_devices")
