#!/usr/bin/env python3
"""Quick script to add missing columns to the database."""
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    database_url = os.getenv("DATABASE_URL", "")
    
    # Convert to asyncpg URL if needed
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(database_url)
    
    sql_statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS kids_mode_enabled BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS parental_pin_hash VARCHAR(255) DEFAULT ''",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255) DEFAULT ''",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(50) DEFAULT 'free'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50) DEFAULT ''",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_ends_at TIMESTAMPTZ DEFAULT NULL",
        "CREATE INDEX IF NOT EXISTS ix_users_stripe_customer_id ON users (stripe_customer_id)",
        "CREATE INDEX IF NOT EXISTS ix_users_subscription_tier ON users (subscription_tier)",
    ]
    
    async with engine.begin() as conn:
        for sql in sql_statements:
            print(f"Executing: {sql}")
            await conn.execute(text(sql))
            print("  ✓ Done")
    
    await engine.dispose()
    print("\n✅ All columns added successfully!")

if __name__ == "__main__":
    asyncio.run(main())
