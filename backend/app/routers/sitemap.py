"""Sitemap generation for SEO."""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Channel, RadioStation
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["sitemap"])


async def generate_sitemap(db: AsyncSession) -> str:
    """Generate sitemap.xml content."""
    # Base URL from settings or default
    base_url = settings.cors_origins_list[0] if settings.cors_origins_list else "https://adajoon.com"
    base_url = base_url.rstrip("/")
    
    # Start sitemap
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    # Homepage (highest priority)
    xml.append("  <url>")
    xml.append(f"    <loc>{base_url}/</loc>")
    xml.append(f"    <lastmod>{datetime.now().date().isoformat()}</lastmod>")
    xml.append("    <changefreq>daily</changefreq>")
    xml.append("    <priority>1.0</priority>")
    xml.append("  </url>")
    
    # TV channels (sample for performance)
    result = await db.execute(
        select(Channel.id, Channel.name, Channel.updated_at)
        .where(Channel.health_status.in_(["verified", "online"]))
        .order_by(Channel.id)
        .limit(1000)
    )
    for channel_id, name, updated_at in result:
        xml.append("  <url>")
        xml.append(f"    <loc>{base_url}/?mode=tv&amp;channel={channel_id}</loc>")
        if updated_at:
            xml.append(f"    <lastmod>{updated_at.date().isoformat()}</lastmod>")
        xml.append("    <changefreq>weekly</changefreq>")
        xml.append("    <priority>0.8</priority>")
        xml.append("  </url>")
    
    # Radio stations (sample for performance)
    result = await db.execute(
        select(RadioStation.id, RadioStation.name, RadioStation.updated_at)
        .where(RadioStation.health_status.in_(["verified", "online"]))
        .order_by(RadioStation.id)
        .limit(1000)
    )
    for station_id, name, updated_at in result:
        xml.append("  <url>")
        xml.append(f"    <loc>{base_url}/?mode=radio&amp;station={station_id}</loc>")
        if updated_at:
            xml.append(f"    <lastmod>{updated_at.date().isoformat()}</lastmod>")
        xml.append("    <changefreq>weekly</changefreq>")
        xml.append("    <priority>0.7</priority>")
        xml.append("  </url>")
    
    xml.append("</urlset>")
    return "\n".join(xml)


@router.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml(db: AsyncSession = Depends(get_db)):
    """Generate and serve sitemap.xml."""
    try:
        content = await generate_sitemap(db)
        return Response(content=content, media_type="application/xml")
    except Exception as e:
        logger.error(f"Failed to generate sitemap: {e}", exc_info=True)
        # Return minimal sitemap on error
        base_url = settings.cors_origins_list[0] if settings.cors_origins_list else "https://adajoon.com"
        base_url = base_url.rstrip("/")
        error_sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base_url}/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>'''
        return Response(content=error_sitemap, media_type="application/xml")


@router.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    """Generate and serve robots.txt."""
    base_url = settings.cors_origins_list[0] if settings.cors_origins_list else "https://adajoon.com"
    base_url = base_url.rstrip("/")
    
    content = f"""User-agent: *
Allow: /

# Sitemap
Sitemap: {base_url}/sitemap.xml

# Crawl delay
Crawl-delay: 1

# Disallow admin/internal endpoints
Disallow: /api/sync
Disallow: /api/validate/
Disallow: /metrics
"""
    return Response(content=content, media_type="text/plain")
