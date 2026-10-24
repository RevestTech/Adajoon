"""
Admin-only authentication middleware.

Ensures that protected routes can only be accessed by admin users.
"""

import logging
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.auth import get_current_user
from app.models import User

logger = logging.getLogger(__name__)


async def require_admin(
    current_user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that requires the current user to be an admin.

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin

    Returns:
        User: The authenticated admin user
    """
    if not current_user:
        logger.warning("Admin endpoint accessed without authentication")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    if not current_user.is_admin and current_user.role != "admin":
        logger.warning(
            "Non-admin user %s attempted to access admin endpoint", current_user.email
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    return current_user


async def require_moderator(
    current_user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that requires the current user to be a moderator or admin.

    Raises:
        HTTPException: 401 if not authenticated, 403 if not moderator/admin

    Returns:
        User: The authenticated moderator/admin user
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    if current_user.role not in ("moderator", "admin") and not current_user.is_admin:
        logger.warning(
            "User %s (role: %s) attempted to access moderator endpoint",
            current_user.email,
            current_user.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator or admin access required",
        )

    return current_user
