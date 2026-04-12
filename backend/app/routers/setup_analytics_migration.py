"""
Temporary one-time endpoint to run analytics migration.
DELETE THIS FILE after running once!
"""
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db

router = APIRouter(prefix="/api/setup", tags=["setup"])
logger = logging.getLogger(__name__)

SETUP_SECRET = "adajoon-analytics-migration-2026"


@router.post("/analytics-migration")
async def run_analytics_migration(
    secret: str,
    db: AsyncSession = Depends(get_db)
):
    """
    One-time endpoint to create analytics_events table.
    
    POST /api/setup/analytics-migration?secret=adajoon-analytics-migration-2026
    
    DELETE THIS ROUTER after running once!
    """
    if secret != SETUP_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid setup secret"
        )
    
    try:
        logger.info("Running analytics migration...")
        
        # Create analytics_events table
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS analytics_events (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                session_id VARCHAR(255) NOT NULL,
                event_name VARCHAR(100) NOT NULL,
                properties JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
            )
        """))
        
        # Create indexes
        await db.execute(text("CREATE INDEX IF NOT EXISTS ix_analytics_events_user_id ON analytics_events (user_id)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS ix_analytics_events_session_id ON analytics_events (session_id)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS ix_analytics_events_event_name ON analytics_events (event_name)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS ix_analytics_events_created_at ON analytics_events (created_at)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS ix_analytics_event_name_created ON analytics_events (event_name, created_at)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS ix_analytics_user_created ON analytics_events (user_id, created_at)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS ix_analytics_session_created ON analytics_events (session_id, created_at)"))
        
        await db.commit()
        
        logger.info("Analytics migration completed successfully!")
        
        return {
            "success": True,
            "message": "Analytics events table created successfully!",
            "warning": "DELETE /backend/app/routers/setup_analytics_migration.py after running this once!"
        }
        
    except Exception as e:
        logger.error(f"Analytics migration failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )
