"""Subscription and billing endpoints."""

import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.csrf import verify_csrf_token
from app.database import get_db
from app.models import User
from app.routers.auth import require_user
from app.services import pricing_service


def _is_allowed_redirect_url(url: str) -> bool:
    """Only allow redirect URLs that point back at our own frontend origins."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False
    origin = f"{parsed.scheme}://{parsed.netloc}"
    return origin in settings.cors_origins


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

# Initialize Stripe
if hasattr(settings, "stripe_secret_key") and settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------


class CheckoutRequest(BaseModel):
    tier: str
    success_url: str
    cancel_url: str
    promo_code: str | None = None

    @field_validator("success_url", "cancel_url")
    @classmethod
    def _validate_redirect_url(cls, v: str) -> str:
        if not _is_allowed_redirect_url(v):
            raise ValueError("URL must point to an allowed app origin")
        return v


class PortalRequest(BaseModel):
    return_url: str

    @field_validator("return_url")
    @classmethod
    def _validate_redirect_url(cls, v: str) -> str:
        if not _is_allowed_redirect_url(v):
            raise ValueError("URL must point to an allowed app origin")
        return v


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/tiers")
async def get_tiers(db: AsyncSession = Depends(get_db)):
    """Get available subscription tiers, as set by an admin in the pricing manager."""
    tiers = await pricing_service.list_tiers(db, active_only=True)
    return {
        "tiers": {
            tier.key: {
                "name": tier.name,
                "price": tier.monthly_price_cents / 100,
                "price_id": tier.stripe_price_id_monthly,
                "features": [
                    f.label for f in sorted(tier.features, key=lambda f: f.sort_order)
                ],
            }
            for tier in tiers
        }
    }


@router.get("/status")
async def get_subscription_status(
    user: User = Depends(require_user),
):
    """Get current user's subscription status."""
    return {
        "tier": user.subscription_tier or "free",
        "status": user.subscription_status or "",
        "ends_at": (
            user.subscription_ends_at.isoformat() if user.subscription_ends_at else None
        ),
        "stripe_customer_id": user.stripe_customer_id or "",
    }


@router.post("/checkout")
async def create_checkout_session(
    request: CheckoutRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    """Create Stripe checkout session for subscription."""
    if not stripe.api_key:
        raise HTTPException(status_code=501, detail="Stripe not configured")

    # Validate tier
    tier = await pricing_service.get_tier_by_key(db, request.tier)
    if not tier or not tier.is_active or request.tier == "free":
        raise HTTPException(status_code=400, detail="Invalid tier")
    if not tier.stripe_price_id_monthly:
        raise HTTPException(
            status_code=400, detail="This tier has no Stripe price configured"
        )

    discount_ids: list[dict] = []
    if request.promo_code:
        discount = await pricing_service.get_active_discount_by_code(
            db, request.promo_code
        )
        if not discount or (discount.tier_id and discount.tier_id != tier.id):
            raise HTTPException(status_code=400, detail="Invalid or expired promo code")
        if discount.stripe_coupon_id:
            discount_ids.append({"coupon": discount.stripe_coupon_id})

    try:
        # Create or retrieve Stripe customer
        if user.stripe_customer_id:
            customer_id = user.stripe_customer_id
        else:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.name,
                metadata={"user_id": str(user.id)},
            )
            customer_id = customer.id
            user.stripe_customer_id = customer_id
            await db.commit()

        # Create checkout session
        session_kwargs = {
            "customer": customer_id,
            "payment_method_types": ["card"],
            "line_items": [
                {
                    "price": tier.stripe_price_id_monthly,
                    "quantity": 1,
                }
            ],
            "mode": "subscription",
            "success_url": request.success_url,
            "cancel_url": request.cancel_url,
            "metadata": {
                "user_id": str(user.id),
                "tier": request.tier,
            },
        }
        if discount_ids:
            session_kwargs["discounts"] = discount_ids
        session = stripe.checkout.Session.create(**session_kwargs)

        if request.promo_code and discount_ids:
            await pricing_service.record_discount_redemption(db, discount)

        return {"checkout_url": session.url, "session_id": session.id}

    except stripe.error.StripeError as e:
        logger.error("Stripe checkout error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/portal")
async def create_portal_session(
    request: PortalRequest,
    user: User = Depends(require_user),
    _csrf: None = Depends(verify_csrf_token),
):
    """Create Stripe customer portal session for managing subscription."""
    if not stripe.api_key:
        raise HTTPException(status_code=501, detail="Stripe not configured")

    if not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No subscription found")

    try:
        session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=request.return_url,
        )

        return {"portal_url": session.url}

    except stripe.error.StripeError as e:
        logger.error("Stripe portal error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Stripe webhook events."""
    if not stripe.api_key:
        raise HTTPException(status_code=501, detail="Stripe not configured")

    if not settings.stripe_webhook_secret:
        logger.error("Stripe webhook secret not configured - rejecting webhook")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        logger.error("Invalid webhook payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle events
    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        # Payment successful, activate subscription
        user_id = int(data["metadata"]["user_id"])
        tier = data["metadata"]["tier"]

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user:
            user.subscription_tier = tier
            user.subscription_status = "active"
            await db.commit()
            logger.info("Subscription activated for user %s: %s", user_id, tier)

    elif event_type == "customer.subscription.updated":
        # Subscription status changed
        customer_id = data["customer"]
        subscription_status = data["status"]

        result = await db.execute(
            select(User).where(User.stripe_customer_id == customer_id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.subscription_status = subscription_status

            # Update tier if subscription is canceled/past_due
            if subscription_status in ("canceled", "unpaid", "past_due"):
                user.subscription_tier = "free"

            # Set end date if subscription is ending
            if data.get("cancel_at"):
                user.subscription_ends_at = datetime.fromtimestamp(
                    data["cancel_at"], tz=timezone.utc
                )

            await db.commit()
            logger.info(
                "Subscription updated for user %s: %s", user.id, subscription_status
            )

    elif event_type == "customer.subscription.deleted":
        # Subscription canceled/expired
        customer_id = data["customer"]

        result = await db.execute(
            select(User).where(User.stripe_customer_id == customer_id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.subscription_tier = "free"
            user.subscription_status = "canceled"
            await db.commit()
            logger.info("Subscription deleted for user %s", user.id)

    return {"status": "processed"}
