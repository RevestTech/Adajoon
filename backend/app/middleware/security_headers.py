"""Security headers middleware for OAuth compatibility."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers that allow OAuth popups to work."""
    
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # Set COOP to allow OAuth popups while maintaining security
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
        response.headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"
        
        return response
