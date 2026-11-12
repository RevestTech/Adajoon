"""Admin audit logging - who did what, when, for the admin-write endpoints
that already exist. Not a generic audit-everything framework."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AdminAuditLog, User


async def log_admin_action(
    db: AsyncSession,
    admin_user: User,
    action: str,
    target_type: str | None = None,
    target_id: object = None,
    detail: str = "",
) -> None:
    """Records one audit row and commits it. Call this after the action's
    own commit so a failed audit write never blocks the action itself."""
    db.add(
        AdminAuditLog(
            admin_user_id=admin_user.id,
            admin_email=admin_user.email,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id is not None else None,
            detail=detail,
        )
    )
    await db.commit()
