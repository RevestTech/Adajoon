"""
Server-side analytics event logging.

Used by routers (e.g. auth) that need to record events originating from the
backend itself (as opposed to client-tracked events sent to /api/analytics).
Failures here must never break the caller's primary flow.
"""
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AnalyticsEvent

logger = logging.getLogger(__name__)


def server_session_id() -> str:
    return f"server-{uuid.uuid4().hex[:12]}"


async def log_auth_event(
    db: AsyncSession,
    event_name: str,
    *,
    user_id: int | None = None,
    session_id: str | None = None,
    properties: dict | None = None,
) -> None:
    """Insert an analytics event without failing the caller's auth flow on error.

    Commits independently of the caller's transaction, so it should be called
    either before any pending writes exist on `db`, or after the caller has
    already committed its own changes.
    """
    try:
        event = AnalyticsEvent(
            user_id=user_id,
            session_id=session_id or server_session_id(),
            event_name=event_name,
            properties=properties or {},
        )
        db.add(event)
        await db.commit()
    except Exception as e:
        logger.error("Failed to log analytics event %s: %s", event_name, e)
        try:
            await db.rollback()
        except Exception:
            pass
