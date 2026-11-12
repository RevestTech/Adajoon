"""Per-tier device-limit enforcement.

The pro/family pricing tiers advertise "5 devices"/"10 devices"
(backend/alembic/versions/012_add_pricing_manager.py's seed data), but
until now nothing actually counted or capped devices - every tier feature
except ad-removal was unenforced. This is deliberately narrow: it enforces
only the device-count promise already made in pricing_features, not a new
product decision. Free/plus have no device-count feature line and so are
left uncapped here, matching what's actually advertised to them.

A "device" is whatever the frontend's persisted per-browser device_id
identifies (see frontend/src/utils/deviceId.js) - logging in again from an
already-known device just refreshes last_seen_at and never counts against
the limit; only a genuinely new device can hit the cap.
"""

import re

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PricingFeature, PricingTier, User, UserDevice

_DEVICE_FEATURE_RE = re.compile(r"^(\d+)_devices$")


async def get_device_limit(db: AsyncSession, tier_key: str) -> int | None:
    """None means unlimited (no `N_devices` feature on this tier)."""
    result = await db.execute(
        select(PricingFeature.key)
        .join(PricingTier, PricingFeature.tier_id == PricingTier.id)
        .where(PricingTier.key == tier_key, PricingFeature.is_active.is_(True))
    )
    for (key,) in result.all():
        match = _DEVICE_FEATURE_RE.match(key)
        if match:
            return int(match.group(1))
    return None


async def enforce_device_limit(
    db: AsyncSession, user: User, device_id: str | None
) -> None:
    """Call right before issuing a session, after the user is resolved but
    before cookies are set, so a blocked login never gets a session.

    device_id is optional so an older/out-of-sync frontend build degrades
    to "unmetered" rather than locking every user out at once - this is a
    new restriction being rolled out, not a security boundary being closed.
    """
    if not device_id:
        return

    limit = await get_device_limit(db, user.subscription_tier or "free")
    if limit is None:
        return

    existing = await db.execute(
        select(UserDevice).where(
            UserDevice.user_id == user.id, UserDevice.device_id == device_id
        )
    )
    device = existing.scalar_one_or_none()
    if device:
        await db.execute(
            UserDevice.__table__.update()
            .where(UserDevice.id == device.id)
            .values(last_seen_at=func.now())
        )
        await db.commit()
        return

    count_result = await db.execute(
        select(func.count())
        .select_from(UserDevice)
        .where(UserDevice.user_id == user.id)
    )
    current_count = count_result.scalar_one()

    if current_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"You've reached your plan's device limit ({limit}). "
                "Remove a device in Settings to log in here."
            ),
        )

    db.add(UserDevice(user_id=user.id, device_id=device_id))
    await db.commit()
