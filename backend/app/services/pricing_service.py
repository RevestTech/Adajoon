from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import PricingDiscount, PricingFeature, PricingTier


async def list_tiers(
    db: AsyncSession, *, active_only: bool = False
) -> list[PricingTier]:
    stmt = select(PricingTier).options(selectinload(PricingTier.features))
    if active_only:
        stmt = stmt.where(PricingTier.is_active.is_(True))
    stmt = stmt.order_by(PricingTier.sort_order)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_tier(db: AsyncSession, tier_id: int) -> PricingTier | None:
    stmt = (
        select(PricingTier)
        .options(selectinload(PricingTier.features))
        .where(PricingTier.id == tier_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_tier_by_key(db: AsyncSession, key: str) -> PricingTier | None:
    stmt = (
        select(PricingTier)
        .options(selectinload(PricingTier.features))
        .where(PricingTier.key == key)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_tier(db: AsyncSession, data: dict) -> PricingTier:
    tier = PricingTier(**data)
    db.add(tier)
    await db.commit()
    await db.refresh(tier)
    tier.features = []
    return tier


async def update_tier(db: AsyncSession, tier: PricingTier, data: dict) -> PricingTier:
    for field, value in data.items():
        if value is not None:
            setattr(tier, field, value)
    await db.commit()
    await db.refresh(tier)
    return tier


async def delete_tier(db: AsyncSession, tier: PricingTier) -> None:
    await db.delete(tier)
    await db.commit()


async def list_features(
    db: AsyncSession, *, tier_id: int | None = None
) -> list[PricingFeature]:
    stmt = select(PricingFeature)
    if tier_id is not None:
        stmt = stmt.where(PricingFeature.tier_id == tier_id)
    stmt = stmt.order_by(PricingFeature.sort_order)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_feature(db: AsyncSession, feature_id: int) -> PricingFeature | None:
    result = await db.execute(
        select(PricingFeature).where(PricingFeature.id == feature_id)
    )
    return result.scalar_one_or_none()


async def create_feature(db: AsyncSession, data: dict) -> PricingFeature:
    feature = PricingFeature(**data)
    db.add(feature)
    await db.commit()
    await db.refresh(feature)
    return feature


async def update_feature(
    db: AsyncSession, feature: PricingFeature, data: dict
) -> PricingFeature:
    for field, value in data.items():
        if value is not None:
            setattr(feature, field, value)
    await db.commit()
    await db.refresh(feature)
    return feature


async def delete_feature(db: AsyncSession, feature: PricingFeature) -> None:
    await db.delete(feature)
    await db.commit()


async def list_discounts(db: AsyncSession) -> list[PricingDiscount]:
    result = await db.execute(
        select(PricingDiscount).order_by(PricingDiscount.created_at.desc())
    )
    return list(result.scalars().all())


async def get_discount(db: AsyncSession, discount_id: int) -> PricingDiscount | None:
    result = await db.execute(
        select(PricingDiscount).where(PricingDiscount.id == discount_id)
    )
    return result.scalar_one_or_none()


async def get_active_discount_by_code(
    db: AsyncSession, code: str
) -> PricingDiscount | None:
    """Look up a usable discount by code - active, within its date window,
    and under its redemption cap (ignored when unset)."""
    result = await db.execute(
        select(PricingDiscount).where(
            PricingDiscount.code == code.strip().upper(),
            PricingDiscount.is_active.is_(True),
        )
    )
    discount = result.scalar_one_or_none()
    if not discount:
        return None

    now = datetime.now(timezone.utc)
    if discount.starts_at and discount.starts_at > now:
        return None
    if discount.ends_at and discount.ends_at < now:
        return None
    if (
        discount.max_redemptions is not None
        and discount.redemption_count >= discount.max_redemptions
    ):
        return None
    return discount


async def create_discount(db: AsyncSession, data: dict) -> PricingDiscount:
    data["code"] = data["code"].strip().upper()
    discount = PricingDiscount(**data)
    db.add(discount)
    await db.commit()
    await db.refresh(discount)
    return discount


async def update_discount(
    db: AsyncSession, discount: PricingDiscount, data: dict
) -> PricingDiscount:
    for field, value in data.items():
        if value is not None:
            setattr(discount, field, value)
    await db.commit()
    await db.refresh(discount)
    return discount


async def delete_discount(db: AsyncSession, discount: PricingDiscount) -> None:
    await db.delete(discount)
    await db.commit()


async def record_discount_redemption(
    db: AsyncSession, discount: PricingDiscount
) -> None:
    discount.redemption_count = (discount.redemption_count or 0) + 1
    await db.commit()
