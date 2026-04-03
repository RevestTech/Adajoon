"""CSRF token endpoints."""
from fastapi import APIRouter, Response

from app.csrf import generate_csrf_token

router = APIRouter(prefix="/api/csrf", tags=["csrf"])


@router.get("/token")
async def get_csrf_token(response: Response):
    """Get a CSRF token for authenticated requests."""
    token = generate_csrf_token()
    
    # Set in cookie for convenience
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,  # Frontend needs to read this
        secure=True,
        samesite="lax",
        max_age=3600,
        path="/",
    )
    
    # Also return in body
    return {"csrf_token": token}


@router.post("/logout")
async def logout(response: Response):
    """Logout and clear auth cookies."""
    response.delete_cookie("auth_token", path="/")
    response.delete_cookie("csrf_token", path="/")
    return {"status": "logged_out"}
