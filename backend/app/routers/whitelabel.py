"""White-label B2B API endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Channel, RadioStation, Tenant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/whitelabel", tags=["whitelabel"])
limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# Tenant Authentication
# ---------------------------------------------------------------------------


async def get_tenant(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """Verify tenant API key and return tenant."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key"
        )

    result = await db.execute(
        select(Tenant).where(Tenant.api_key == x_api_key, Tenant.is_active.is_(True))
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )

    return tenant


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------


class BrandingResponse(BaseModel):
    slug: str
    name: str
    logo_url: str
    primary_color: str
    secondary_color: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/branding")
@limiter.limit("30/minute")
async def get_branding(
    request: Request,
    tenant: Tenant = Depends(get_tenant),
):
    """Get branding configuration for tenant."""
    return {
        "slug": tenant.slug,
        "name": tenant.name,
        "logo_url": tenant.logo_url,
        "primary_color": tenant.primary_color,
        "secondary_color": tenant.secondary_color,
    }


@router.get("/channels")
@limiter.limit("30/minute")
async def get_tenant_channels(
    request: Request,
    tenant: Tenant = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
    category: Optional[str] = None,
    country: Optional[str] = None,
):
    """Get channels for tenant (respects tenant limits)."""
    query = select(Channel).where(Channel.health_status.in_(["verified", "online"]))

    # Apply filters
    if category:
        query = query.where(Channel.categories.ilike(f"%{category}%"))
    if country:
        query = query.where(Channel.country_code == country)

    # Apply tenant channel limit
    limit = min(limit, tenant.max_channels)

    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    channels = result.scalars().all()

    return {
        "tenant": tenant.slug,
        "limit": limit,
        "offset": offset,
        "channels": [
            {
                "id": ch.id,
                "name": ch.name,
                "logo": ch.logo,
                "country": ch.country_code,
                "categories": ch.categories,
                "stream_url": ch.stream_url,
            }
            for ch in channels
        ],
    }


@router.get("/radio")
@limiter.limit("30/minute")
async def get_tenant_radio(
    request: Request,
    tenant: Tenant = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
    country: Optional[str] = None,
    tag: Optional[str] = None,
):
    """Get radio stations for tenant (respects tenant limits)."""
    query = select(RadioStation).where(
        RadioStation.health_status.in_(["verified", "online"])
    )

    # Apply filters
    if country:
        query = query.where(RadioStation.country_code == country)
    if tag:
        query = query.where(RadioStation.tags.ilike(f"%{tag}%"))

    # Apply tenant channel limit
    limit = min(limit, tenant.max_channels)

    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    stations = result.scalars().all()

    return {
        "tenant": tenant.slug,
        "limit": limit,
        "offset": offset,
        "stations": [
            {
                "id": st.id,
                "name": st.name,
                "favicon": st.favicon,
                "country": st.country,
                "country_code": st.country_code,
                "tags": st.tags,
                "url": st.url_resolved or st.url,
            }
            for st in stations
        ],
    }


@router.get("/stats")
@limiter.limit("30/minute")
async def get_tenant_stats(
    request: Request,
    tenant: Tenant = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get usage statistics for tenant."""
    channel_count = (
        await db.execute(
            select(func.count(Channel.id)).where(
                Channel.health_status.in_(["verified", "online"])
            )
        )
    ).scalar() or 0

    radio_count = (
        await db.execute(
            select(func.count(RadioStation.id)).where(
                RadioStation.health_status.in_(["verified", "online"])
            )
        )
    ).scalar() or 0

    return {
        "tenant": tenant.slug,
        "limits": {
            "max_channels": tenant.max_channels,
            "max_requests_per_day": tenant.max_requests_per_day,
        },
        "available": {
            "channels": min(channel_count, tenant.max_channels),
            "radio": min(radio_count, tenant.max_channels),
        },
    }
