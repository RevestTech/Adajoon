"""Security headers middleware for OAuth compatibility."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add comprehensive security headers while allowing OAuth popups."""
    
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # COOP/COEP - Allow OAuth popups while maintaining security
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
        response.headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Clickjacking protection
        response.headers["X-Frame-Options"] = "DENY"
        
        # XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions policy - disable unused features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), usb=(), "
            "magnetometer=(), gyroscope=(), accelerometer=()"
        )
        
        # Content Security Policy (production only)
        if settings.env == "production":
            # CSP tailored for your streaming app
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Needed for React
                "style-src 'self' 'unsafe-inline'",  # Needed for styled components
                "img-src 'self' data: https:",  # Allow external logos/images
                "media-src 'self' blob: https:",  # Allow streaming from external sources
                "connect-src 'self' https://iptv-org.github.io https://de1.api.radio-browser.info https://raw.githubusercontent.com",  # API endpoints
                "font-src 'self' data:",
                "object-src 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "frame-ancestors 'none'",
                "upgrade-insecure-requests",
            ]
            response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # HSTS (HTTP Strict Transport Security) - production only
        if settings.env == "production":
            # max-age=2 years, includeSubDomains, preload
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        
        return response
