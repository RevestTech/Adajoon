"""Subscription and billing endpoints."""
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import stripe

from app.database import get_db
from app.config import settings
from app.models import User
from app.routers.auth import require_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

# Initialize Stripe
if hasattr(settings, 'stripe_secret_key') and settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key


# ---------------------------------------------------------------------------
# Subscription Tiers
# ---------------------------------------------------------------------------

TIERS = {
    "free": {
        "name": "Free",
        "price": 0,
        "features": ["Unlimited streaming", "Ads supported"],
    },
    "plus": {
        "name": "Plus",
        "price": 4.99,
        "price_id": "price_plus_monthly",  # Replace with actual Stripe price ID
        "features": ["No ads", "HD quality", "Unlimited streaming"],
    },
    "pro": {
        "name": "Pro",
        "price": 9.99,
        "price_id": "price_pro_monthly",
        "features": ["No ads", "4K quality", "Offline downloads", "5 devices"],
    },
    "family": {
        "name": "Family",
        "price": 14.99,
        "price_id": "price_family_monthly",
        "features": ["No ads", "4K quality", "Offline downloads", "10 devices", "6 profiles"],
    },
}


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class CheckoutRequest(BaseModel):
    tier: str
    success_url: str
    cancel_url: str


class PortalRequest(BaseModel):
    return_url: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/tiers")
async def get_tiers():
    """Get available subscription tiers."""
    return {"tiers": TIERS}


@router.get("/status")
async def get_subscription_status(
    user: User = Depends(require_user),
):
    """Get current user's subscription status."""
    return {
        "tier": user.subscription_tier or "free",
        "status": user.subscription_status or "",
        "ends_at": user.subscription_ends_at.isoformat() if user.subscription_ends_at else None,
        "stripe_customer_id": user.stripe_customer_id or "",
    }


@router.post("/checkout")
async def create_checkout_session(
    request: CheckoutRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Create Stripe checkout session for subscription."""
    if not stripe.api_key:
        raise HTTPException(
            status_code=501,
            detail="Stripe not configured"
        )
    
    # Validate tier
    if request.tier not in TIERS or request.tier == "free":
        raise HTTPException(
            status_code=400,
            detail="Invalid tier"
        )
    
    tier_info = TIERS[request.tier]
    
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
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": tier_info["price_id"],
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                "user_id": str(user.id),
                "tier": request.tier,
            },
        )
        
        return {"checkout_url": session.url, "session_id": session.id}
    
    except stripe.error.StripeError as e:
        logger.error("Stripe checkout error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/portal")
async def create_portal_session(
    request: PortalRequest,
    user: User = Depends(require_user),
):
    """Create Stripe customer portal session for managing subscription."""
    if not stripe.api_key:
        raise HTTPException(status_code=501, detail="Stripe not configured")
    
    if not user.stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail="No subscription found"
        )
    
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
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    webhook_secret = getattr(settings, 'stripe_webhook_secret', '')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
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
            logger.info("Subscription updated for user %s: %s", user.id, subscription_status)
    
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
