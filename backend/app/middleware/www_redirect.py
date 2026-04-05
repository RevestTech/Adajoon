"""Redirect non-www to www domain in production."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from app.config import settings


class WWWRedirectMiddleware(BaseHTTPMiddleware):
    """Redirect adajoon.com to www.adajoon.com in production."""
    
    async def dispatch(self, request: Request, call_next):
        if settings.env == "production":
            host = request.headers.get("host", "")
            
            # Redirect adajoon.com -> www.adajoon.com
            if host == "adajoon.com":
                url = str(request.url).replace("adajoon.com", "www.adajoon.com", 1)
                return RedirectResponse(url=url, status_code=301)
        
        return await call_next(request)
