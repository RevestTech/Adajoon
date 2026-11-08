"""Admin-only API endpoints for user and subscription management."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.csrf import verify_csrf_token
from app.database import get_db
from app.middleware.admin_required import require_admin
from app.models import PricingTier, User

router = APIRouter(prefix="/api/admin", tags=["admin", "users"])
logger = logging.getLogger(__name__)


def _ilike_pattern(raw: str) -> str:
    """Escape ILIKE wildcard/escape characters in user input so a search for
    literal `%`, `_`, or `\\` doesn't act as a wildcard."""
    escaped = raw.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


@router.post("/users/{user_id}/make-admin")
async def make_user_admin(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    """
    Grant admin privileges to a user.

    Requires admin access.
    """
    logger.info("Admin %s granting admin to user ID %d", admin_user.email, user_id)

    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    target_user.is_admin = True
    target_user.role = "admin"
    await db.commit()

    logger.info("User %s is now an admin", target_user.email)

    return {
        "success": True,
        "user_id": user_id,
        "email": target_user.email,
        "is_admin": True,
    }


@router.post("/users/{user_id}/revoke-admin")
async def revoke_user_admin(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    """
    Revoke admin privileges from a user.

    Requires admin access.
    """
    logger.info("Admin %s revoking admin from user ID %d", admin_user.email, user_id)

    # Prevent self-demotion
    if admin_user.id == user_id:
        raise HTTPException(
            status_code=400, detail="Cannot revoke your own admin privileges"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    target_user.is_admin = False
    target_user.role = "user"
    await db.commit()

    logger.info("Admin privileges revoked for user %s", target_user.email)

    return {
        "success": True,
        "user_id": user_id,
        "email": target_user.email,
        "is_admin": False,
    }


@router.get("/users")
async def list_users(
    q: str | None = Query(default=None, description="Search by email or name"),
    tier: str | None = Query(default=None),
    admin_only: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Search/list users for support and account management."""
    stmt = select(User)
    count_stmt = select(func.count(User.id))

    if q:
        pattern = _ilike_pattern(q)
        cond = or_(
            User.email.ilike(pattern, escape="\\"),
            User.name.ilike(pattern, escape="\\"),
        )
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    if tier:
        stmt = stmt.where(User.subscription_tier == tier)
        count_stmt = count_stmt.where(User.subscription_tier == tier)
    if admin_only:
        stmt = stmt.where(User.is_admin.is_(True))
        count_stmt = count_stmt.where(User.is_admin.is_(True))

    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = (
        stmt.order_by(User.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    users = (await db.execute(stmt)).scalars().all()

    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "name": u.name,
                "is_admin": u.is_admin,
                "subscription_tier": u.subscription_tier,
                "subscription_status": u.subscription_status,
                "subscription_ends_at": (
                    u.subscription_ends_at.isoformat()
                    if u.subscription_ends_at
                    else None
                ),
                "stripe_customer_id": u.stripe_customer_id or "",
                "kids_mode_enabled": u.kids_mode_enabled,
                "has_parental_pin": bool(u.parental_pin_hash),
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login_at": (
                    u.last_login_at.isoformat() if u.last_login_at else None
                ),
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


class UserAdminUpdate(BaseModel):
    subscription_tier: str | None = None
    subscription_status: str | None = None
    subscription_ends_at: datetime | None = None
    clear_parental_pin: bool = False


@router.patch("/users/{user_id}")
async def admin_update_user(
    user_id: int,
    payload: UserAdminUpdate,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    """Comp/revoke a subscription or clear a locked-out parental PIN.

    Writes directly to the User row rather than Stripe - for manual grants
    (press, partners, support goodwill) and support overrides, not for
    managing a real paid subscription (use the Stripe dashboard for that;
    the existing webhook handler keeps real subscriptions in sync with
    these same fields).
    """
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.subscription_tier is not None:
        if payload.subscription_tier != "free":
            tier_exists = (
                await db.execute(
                    select(PricingTier.key).where(
                        PricingTier.key == payload.subscription_tier
                    )
                )
            ).scalar_one_or_none()
            if not tier_exists:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown subscription_tier: {payload.subscription_tier!r}",
                )
        target.subscription_tier = payload.subscription_tier
    if payload.subscription_status is not None:
        target.subscription_status = payload.subscription_status
    if payload.subscription_ends_at is not None:
        target.subscription_ends_at = payload.subscription_ends_at
    if payload.clear_parental_pin:
        target.parental_pin_hash = ""
        target.kids_mode_enabled = False

    await db.commit()
    logger.info("Admin %s updated user %s", admin_user.email, target.email)
    return {"success": True}


@router.get("/subscriptions")
async def list_subscriptions(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Everyone with a non-free tier or a subscription status - comped
    accounts included. Stripe stays the source of truth for billing;
    this is a read view plus the comp/revoke actions on /users/{id}."""
    result = await db.execute(
        select(User)
        .where(or_(User.subscription_tier != "free", User.subscription_status != ""))
        .order_by(User.subscription_ends_at.desc().nulls_last())
    )
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "tier": u.subscription_tier,
            "status": u.subscription_status,
            "ends_at": (
                u.subscription_ends_at.isoformat() if u.subscription_ends_at else None
            ),
            "stripe_customer_id": u.stripe_customer_id or "",
        }
        for u in users
    ]


@router.get("/revenue")
async def get_revenue_summary(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Rough current MRR: active/comped subscribers per tier times that
    tier's current price. Not a Stripe reconciliation - just enough signal
    for a tiny team to see if the business is moving."""
    result = await db.execute(
        select(
            User.subscription_tier,
            func.count(User.id).label("count"),
        )
        .where(User.subscription_tier != "free")
        .where(User.subscription_status == "active")
        .group_by(User.subscription_tier)
    )
    counts_by_tier = {row.subscription_tier: row.count for row in result.all()}

    tiers_result = await db.execute(select(PricingTier))
    tiers = tiers_result.scalars().all()

    breakdown = []
    mrr_cents = 0
    for t in tiers:
        count = counts_by_tier.get(t.key, 0)
        tier_mrr_cents = count * t.monthly_price_cents
        mrr_cents += tier_mrr_cents
        if count:
            breakdown.append(
                {
                    "tier": t.key,
                    "subscribers": count,
                    "mrr": tier_mrr_cents / 100,
                }
            )

    return {"mrr": mrr_cents / 100, "breakdown": breakdown}
