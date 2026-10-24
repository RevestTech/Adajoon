"""CSRF protection utilities."""

import hmac
import secrets
from typing import Optional

from fastapi import HTTPException, Request, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import settings

# CSRF token serializer
csrf_serializer = URLSafeTimedSerializer(settings.jwt_secret, salt="csrf-token")

# CSRF token max age (1 hour)
CSRF_TOKEN_MAX_AGE = 3600


def generate_csrf_token() -> str:
    """Generate a new CSRF token."""
    random_string = secrets.token_urlsafe(32)
    return csrf_serializer.dumps(random_string)


def validate_csrf_token(token: str, max_age: int = CSRF_TOKEN_MAX_AGE) -> bool:
    """Validate a CSRF token."""
    try:
        csrf_serializer.loads(token, max_age=max_age)
        return True
    except (BadSignature, SignatureExpired):
        return False


async def verify_csrf_token(request: Request) -> None:
    """Dependency to verify CSRF token on mutating requests."""
    # Skip CSRF for GET, HEAD, OPTIONS
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return

    # Bearer-authenticated requests aren't vulnerable to CSRF: a browser can't
    # be made to attach an Authorization header to a cross-site request, so
    # the double-submit cookie check below only applies to cookie auth.
    if request.headers.get("Authorization"):
        return

    # Get CSRF token from header
    csrf_token = request.headers.get("X-CSRF-Token")
    if not csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Missing CSRF token"
        )

    # Double-submit check: header token must match the cookie the server issued
    cookie_token = request.cookies.get("csrf_token")
    if not cookie_token or not hmac.compare_digest(csrf_token, cookie_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token does not match session",
        )

    # Validate token
    if not validate_csrf_token(csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired CSRF token",
        )
