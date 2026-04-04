"""Security headers middleware for OAuth compatibility."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add comprehensive security headers while allowing OAuth popups."""
    
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # COOP/COEP - Must be permissive for OAuth popups to work
        # Note: Google/Apple OAuth requires window.postMessage which COOP blocks
        # Setting to unsafe-none allows OAuth while still maintaining other security
        response.headers["Cross-Origin-Opener-Policy"] = "unsafe-none"
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
            # CSP tailored for your streaming app with OAuth support
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://accounts.google.com https://appleid.cdn-apple.com https://www.gstatic.com https://imasdk.googleapis.com",  # OAuth + Chromecast + IMA SDK
                "style-src 'self' 'unsafe-inline' https://accounts.google.com https://appleid.cdn-apple.com https://fonts.googleapis.com",  # OAuth + Google Fonts
                "img-src 'self' data: https:",  # Allow external logos/images
                "media-src 'self' blob: https:",  # Allow streaming from external sources
                "connect-src 'self' https://iptv-org.github.io https://de1.api.radio-browser.info https://raw.githubusercontent.com https://accounts.google.com https://appleid.apple.com",  # OAuth + API endpoints
                "font-src 'self' data: https://fonts.gstatic.com",  # Google Fonts font files
                "object-src 'none'",
                "base-uri 'self'",
                "form-action 'self' https://accounts.google.com https://appleid.apple.com",  # OAuth form actions
                "frame-src 'self' https://accounts.google.com https://appleid.apple.com",  # OAuth iframes
                "frame-ancestors 'none'",
                "upgrade-insecure-requests",
            ]
            response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # HSTS (HTTP Strict Transport Security) - production only
        if settings.env == "production":
            # max-age=2 years, includeSubDomains, preload
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        
        return response
