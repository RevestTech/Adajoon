"""Add pricing_tiers, pricing_features, pricing_discounts for the admin pricing manager

Revision ID: 012
Revises: 011
Create Date: 2026-10-24

"""

from alembic import op

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS pricing_tiers (
            id SERIAL PRIMARY KEY,
            key VARCHAR(50) NOT NULL UNIQUE,
            name VARCHAR(100) NOT NULL,
            monthly_price_cents INTEGER NOT NULL DEFAULT 0,
            annual_price_cents INTEGER,
            stripe_price_id_monthly VARCHAR(255) DEFAULT '',
            stripe_price_id_annual VARCHAR(255) DEFAULT '',
            sort_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_pricing_tiers_key ON pricing_tiers (key)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_pricing_tiers_sort_order ON pricing_tiers (sort_order)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_pricing_tiers_is_active ON pricing_tiers (is_active)"
    )

    op.execute("""
        CREATE TABLE IF NOT EXISTS pricing_features (
            id SERIAL PRIMARY KEY,
            tier_id INTEGER REFERENCES pricing_tiers(id) ON DELETE CASCADE,
            key VARCHAR(100) NOT NULL,
            label VARCHAR(255) NOT NULL,
            is_addon BOOLEAN DEFAULT FALSE,
            addon_price_cents INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT now(),
            CONSTRAINT uq_pricing_feature_tier_key UNIQUE (tier_id, key)
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_pricing_features_tier_id ON pricing_features (tier_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_pricing_features_key ON pricing_features (key)"
    )

    op.execute("""
        CREATE TABLE IF NOT EXISTS pricing_discounts (
            id SERIAL PRIMARY KEY,
            code VARCHAR(50) NOT NULL UNIQUE,
            label VARCHAR(255) DEFAULT '',
            percent_off INTEGER,
            amount_off_cents INTEGER,
            tier_id INTEGER REFERENCES pricing_tiers(id) ON DELETE CASCADE,
            stripe_coupon_id VARCHAR(255) DEFAULT '',
            starts_at TIMESTAMPTZ,
            ends_at TIMESTAMPTZ,
            max_redemptions INTEGER,
            redemption_count INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_pricing_discounts_code ON pricing_discounts (code)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_pricing_discounts_tier_id ON pricing_discounts (tier_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_pricing_discounts_is_active ON pricing_discounts (is_active)"
    )

    # Seed the four tiers that were previously hardcoded in subscriptions.py,
    # so existing checkout/price behavior is unchanged once the API switches
    # to reading from these tables.
    op.execute("""
        INSERT INTO pricing_tiers (key, name, monthly_price_cents, sort_order, stripe_price_id_monthly)
        VALUES
            ('free', 'Free', 0, 0, ''),
            ('plus', 'Plus', 499, 1, 'price_plus_monthly'),
            ('pro', 'Pro', 999, 2, 'price_pro_monthly'),
            ('family', 'Family', 1499, 3, 'price_family_monthly')
        ON CONFLICT (key) DO NOTHING
    """)

    op.execute("""
        INSERT INTO pricing_features (tier_id, key, label, sort_order)
        SELECT t.id, f.key, f.label, f.sort_order
        FROM pricing_tiers t
        JOIN (VALUES
            ('free', 'unlimited_streaming', 'Unlimited streaming', 0),
            ('free', 'ads_supported', 'Ads supported', 1),
            ('plus', 'no_ads', 'No ads', 0),
            ('plus', 'hd_quality', 'HD quality', 1),
            ('plus', 'unlimited_streaming', 'Unlimited streaming', 2),
            ('pro', 'no_ads', 'No ads', 0),
            ('pro', '4k_quality', '4K quality', 1),
            ('pro', 'offline_downloads', 'Offline downloads', 2),
            ('pro', '5_devices', '5 devices', 3),
            ('family', 'no_ads', 'No ads', 0),
            ('family', '4k_quality', '4K quality', 1),
            ('family', 'offline_downloads', 'Offline downloads', 2),
            ('family', '10_devices', '10 devices', 3),
            ('family', '6_profiles', '6 profiles', 4)
        ) AS f(tier_key, key, label, sort_order) ON f.tier_key = t.key
        ON CONFLICT (tier_id, key) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS pricing_discounts")
    op.execute("DROP TABLE IF EXISTS pricing_features")
    op.execute("DROP TABLE IF EXISTS pricing_tiers")
