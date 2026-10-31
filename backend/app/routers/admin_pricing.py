"""Admin-only CRUD for subscription tiers, feature add-ons, and discount codes.

Lets an admin (is_admin / role="admin") set pricing and run promotions from
the admin dashboard instead of editing hardcoded values in subscriptions.py.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.csrf import verify_csrf_token
from app.database import get_db
from app.middleware.admin_required import require_admin
from app.models import User
from app.schemas import (
    PricingDiscountCreate,
    PricingDiscountOut,
    PricingDiscountUpdate,
    PricingFeatureCreate,
    PricingFeatureOut,
    PricingFeatureUpdate,
    PricingTierCreate,
    PricingTierOut,
    PricingTierUpdate,
)
from app.services import pricing_service, settings_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/pricing", tags=["admin", "pricing"])


# ---------------------------------------------------------------------------
# Monetization settings (ads kill switch)
# ---------------------------------------------------------------------------


class AdsSettingUpdate(BaseModel):
    ads_enabled: bool


@router.get("/settings")
async def admin_get_pricing_settings(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return {
        "ads_enabled": await settings_service.get_bool_setting(db, "ads_enabled", True)
    }


@router.patch("/settings")
async def admin_update_pricing_settings(
    payload: AdsSettingUpdate,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    await settings_service.set_bool_setting(db, "ads_enabled", payload.ads_enabled)
    logger.info("Admin %s set ads_enabled=%s", admin_user.email, payload.ads_enabled)
    return {"ads_enabled": payload.ads_enabled}


# ---------------------------------------------------------------------------
# Tiers
# ---------------------------------------------------------------------------


@router.get("/tiers", response_model=list[PricingTierOut])
async def admin_list_tiers(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await pricing_service.list_tiers(db)


@router.post("/tiers", response_model=PricingTierOut)
async def admin_create_tier(
    payload: PricingTierCreate,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    if await pricing_service.get_tier_by_key(db, payload.key):
        raise HTTPException(
            status_code=409, detail="A tier with this key already exists"
        )
    tier = await pricing_service.create_tier(db, payload.model_dump())
    logger.info("Admin %s created pricing tier %s", admin_user.email, tier.key)
    return tier


@router.patch("/tiers/{tier_id}", response_model=PricingTierOut)
async def admin_update_tier(
    tier_id: int,
    payload: PricingTierUpdate,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    tier = await pricing_service.get_tier(db, tier_id)
    if not tier:
        raise HTTPException(status_code=404, detail="Tier not found")
    tier = await pricing_service.update_tier(
        db, tier, payload.model_dump(exclude_unset=True)
    )
    logger.info("Admin %s updated pricing tier %s", admin_user.email, tier.key)
    return tier


@router.delete("/tiers/{tier_id}")
async def admin_delete_tier(
    tier_id: int,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    tier = await pricing_service.get_tier(db, tier_id)
    if not tier:
        raise HTTPException(status_code=404, detail="Tier not found")
    await pricing_service.delete_tier(db, tier)
    logger.info("Admin %s deleted pricing tier %s", admin_user.email, tier.key)
    return {"success": True}


# ---------------------------------------------------------------------------
# Features (bundled-in tier features, or standalone paid add-ons)
# ---------------------------------------------------------------------------


@router.get("/features", response_model=list[PricingFeatureOut])
async def admin_list_features(
    tier_id: int | None = None,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await pricing_service.list_features(db, tier_id=tier_id)


@router.post("/features", response_model=PricingFeatureOut)
async def admin_create_feature(
    payload: PricingFeatureCreate,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    if payload.tier_id is not None and not await pricing_service.get_tier(
        db, payload.tier_id
    ):
        raise HTTPException(status_code=404, detail="Tier not found")
    feature = await pricing_service.create_feature(db, payload.model_dump())
    logger.info("Admin %s created pricing feature %s", admin_user.email, feature.key)
    return feature


@router.patch("/features/{feature_id}", response_model=PricingFeatureOut)
async def admin_update_feature(
    feature_id: int,
    payload: PricingFeatureUpdate,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    feature = await pricing_service.get_feature(db, feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    feature = await pricing_service.update_feature(
        db, feature, payload.model_dump(exclude_unset=True)
    )
    logger.info("Admin %s updated pricing feature %s", admin_user.email, feature.key)
    return feature


@router.delete("/features/{feature_id}")
async def admin_delete_feature(
    feature_id: int,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    feature = await pricing_service.get_feature(db, feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    await pricing_service.delete_feature(db, feature)
    logger.info("Admin %s deleted pricing feature %s", admin_user.email, feature.key)
    return {"success": True}


# ---------------------------------------------------------------------------
# Discounts
# ---------------------------------------------------------------------------


@router.get("/discounts", response_model=list[PricingDiscountOut])
async def admin_list_discounts(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await pricing_service.list_discounts(db)


@router.post("/discounts", response_model=PricingDiscountOut)
async def admin_create_discount(
    payload: PricingDiscountCreate,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    if payload.percent_off is None and payload.amount_off_cents is None:
        raise HTTPException(
            status_code=400, detail="Set either percent_off or amount_off_cents"
        )
    if payload.tier_id is not None and not await pricing_service.get_tier(
        db, payload.tier_id
    ):
        raise HTTPException(status_code=404, detail="Tier not found")

    existing = await pricing_service.get_active_discount_by_code(db, payload.code)
    if existing:
        raise HTTPException(
            status_code=409, detail="A discount with this code already exists"
        )

    discount = await pricing_service.create_discount(db, payload.model_dump())
    logger.info("Admin %s created discount code %s", admin_user.email, discount.code)
    return discount


@router.patch("/discounts/{discount_id}", response_model=PricingDiscountOut)
async def admin_update_discount(
    discount_id: int,
    payload: PricingDiscountUpdate,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    discount = await pricing_service.get_discount(db, discount_id)
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found")
    discount = await pricing_service.update_discount(
        db, discount, payload.model_dump(exclude_unset=True)
    )
    logger.info("Admin %s updated discount code %s", admin_user.email, discount.code)
    return discount


@router.delete("/discounts/{discount_id}")
async def admin_delete_discount(
    discount_id: int,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    discount = await pricing_service.get_discount(db, discount_id)
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found")
    await pricing_service.delete_discount(db, discount)
    logger.info("Admin %s deleted discount code %s", admin_user.email, discount.code)
    return {"success": True}
