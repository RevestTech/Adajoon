-- Add missing columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS kids_mode_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS parental_pin_hash VARCHAR(255) DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255) DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(50) DEFAULT 'free';
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50) DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_ends_at TIMESTAMPTZ DEFAULT NULL;

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_users_stripe_customer_id ON users (stripe_customer_id);
CREATE INDEX IF NOT EXISTS ix_users_subscription_tier ON users (subscription_tier);
