"""CSRF token endpoints."""
from fastapi import APIRouter, Request, Response

from app.csrf import generate_csrf_token
from app.config import settings

router = APIRouter(prefix="/api/csrf", tags=["csrf"])


def _cookie_domain_for_host(host: str | None) -> str | None:
    if settings.env != "production":
        return None
    h = (host or "").split(":")[0].lower()
    if h == "adajoon.com" or h.endswith(".adajoon.com"):
        return ".adajoon.com"
    return None


@router.get("/token")
async def get_csrf_token(request: Request, response: Response):
    """Get a CSRF token for authenticated requests."""
    token = generate_csrf_token()
    cookie_domain = _cookie_domain_for_host(request.headers.get("host"))

    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,
        secure=True,
        samesite="lax",
        max_age=3600,
        path="/",
        domain=cookie_domain,
    )

    return {"csrf_token": token}


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout and clear auth cookies."""
    cookie_domain = _cookie_domain_for_host(request.headers.get("host"))
    response.delete_cookie("auth_token", path="/", domain=cookie_domain)
    response.delete_cookie("csrf_token", path="/", domain=cookie_domain)
    # Also clear legacy host-only cookies if domain cookie was used previously
    if cookie_domain:
        response.delete_cookie("auth_token", path="/")
        response.delete_cookie("csrf_token", path="/")
    return {"status": "logged_out"}
