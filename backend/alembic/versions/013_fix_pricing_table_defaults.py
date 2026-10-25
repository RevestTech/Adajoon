"""Fix pricing_tiers/pricing_features/pricing_discounts missing column defaults

Revision ID: 013
Revises: 012
Create Date: 2026-10-25

app/main.py runs Base.metadata.create_all() on startup, which created these
tables from the SQLAlchemy models (Python-side `default=`, not a real
DEFAULT) before migration 012 ever ran. Its `CREATE TABLE IF NOT EXISTS`
was a no-op against the already-existing tables, so the seed INSERTs -
which omit is_active/stripe_price_id_annual/is_addon/addon_price_cents -
wrote NULL instead of falling back to a default that was never actually
in the database. This sets real DB-level defaults (idempotent even if 012
already set them) and backfills the NULL rows 012 seeded.
"""

from alembic import op

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE pricing_tiers ALTER COLUMN stripe_price_id_annual SET DEFAULT '';"
    )
    op.execute("ALTER TABLE pricing_tiers ALTER COLUMN is_active SET DEFAULT TRUE;")
    op.execute(
        "UPDATE pricing_tiers SET stripe_price_id_annual = '' WHERE stripe_price_id_annual IS NULL;"
    )
    op.execute("UPDATE pricing_tiers SET is_active = TRUE WHERE is_active IS NULL;")

    op.execute("ALTER TABLE pricing_features ALTER COLUMN is_addon SET DEFAULT FALSE;")
    op.execute(
        "ALTER TABLE pricing_features ALTER COLUMN addon_price_cents SET DEFAULT 0;"
    )
    op.execute("ALTER TABLE pricing_features ALTER COLUMN is_active SET DEFAULT TRUE;")
    op.execute("UPDATE pricing_features SET is_addon = FALSE WHERE is_addon IS NULL;")
    op.execute(
        "UPDATE pricing_features SET addon_price_cents = 0 WHERE addon_price_cents IS NULL;"
    )
    op.execute("UPDATE pricing_features SET is_active = TRUE WHERE is_active IS NULL;")

    op.execute(
        "ALTER TABLE pricing_discounts ALTER COLUMN redemption_count SET DEFAULT 0;"
    )
    op.execute("ALTER TABLE pricing_discounts ALTER COLUMN is_active SET DEFAULT TRUE;")
    op.execute(
        "UPDATE pricing_discounts SET redemption_count = 0 WHERE redemption_count IS NULL;"
    )
    op.execute("UPDATE pricing_discounts SET is_active = TRUE WHERE is_active IS NULL;")


def downgrade() -> None:
    # Defaults/backfill are not worth reversing - nothing destructive to undo.
    pass
