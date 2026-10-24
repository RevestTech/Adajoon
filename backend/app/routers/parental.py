"""Parental controls endpoints."""

from typing import Optional

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.csrf import verify_csrf_token
from app.database import get_db
from app.models import User
from app.routers.auth import require_user

router = APIRouter(prefix="/api/parental", tags=["parental"])
limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------


class SetPinRequest(BaseModel):
    pin: str  # 4-6 digit PIN


class VerifyPinRequest(BaseModel):
    pin: str


class UpdateModeRequest(BaseModel):
    enabled: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/status")
async def get_parental_status(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Get parental control status for current user."""
    return {
        "kids_mode_enabled": user.kids_mode_enabled,
        "has_pin": bool(user.parental_pin_hash),
    }


@router.post("/set-pin")
async def set_parental_pin(
    request: SetPinRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    """Set or update parental control PIN."""
    # Validate PIN format (4-6 digits)
    if not request.pin.isdigit() or len(request.pin) < 4 or len(request.pin) > 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="PIN must be 4-6 digits"
        )

    # Hash PIN with bcrypt
    pin_hash = bcrypt.hashpw(request.pin.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )

    # Update user
    user.parental_pin_hash = pin_hash
    await db.commit()

    return {"status": "pin_set"}


@router.post("/verify-pin")
@limiter.limit("10/minute")
async def verify_parental_pin(
    http_request: Request,
    request: VerifyPinRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    """Verify parental control PIN."""
    if not user.parental_pin_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No PIN set"
        )

    # Verify PIN
    try:
        valid = bcrypt.checkpw(
            request.pin.encode("utf-8"), user.parental_pin_hash.encode("utf-8")
        )
    except Exception:
        valid = False

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid PIN"
        )

    return {"status": "verified"}


@router.post("/kids-mode")
async def toggle_kids_mode(
    request: UpdateModeRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    """Enable or disable kids mode."""
    user.kids_mode_enabled = request.enabled
    await db.commit()

    return {
        "kids_mode_enabled": user.kids_mode_enabled,
    }


@router.delete("/pin")
@limiter.limit("10/minute")
async def remove_parental_pin(
    http_request: Request,
    request: VerifyPinRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    """Remove parental control PIN. Requires the current PIN."""
    if not user.parental_pin_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No PIN set"
        )

    try:
        valid = bcrypt.checkpw(
            request.pin.encode("utf-8"), user.parental_pin_hash.encode("utf-8")
        )
    except Exception:
        valid = False

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid PIN"
        )

    user.parental_pin_hash = ""
    user.kids_mode_enabled = False
    await db.commit()

    return {"status": "pin_removed"}
