"""Parental controls endpoints."""
import bcrypt
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models import User
from app.routers.auth import require_user

router = APIRouter(prefix="/api/parental", tags=["parental"])


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
):
    """Set or update parental control PIN."""
    # Validate PIN format (4-6 digits)
    if not request.pin.isdigit() or len(request.pin) < 4 or len(request.pin) > 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN must be 4-6 digits"
        )
    
    # Hash PIN with bcrypt
    pin_hash = bcrypt.hashpw(request.pin.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Update user
    user.parental_pin_hash = pin_hash
    await db.commit()
    
    return {"status": "pin_set"}


@router.post("/verify-pin")
async def verify_parental_pin(
    request: VerifyPinRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify parental control PIN."""
    if not user.parental_pin_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No PIN set"
        )
    
    # Verify PIN
    try:
        valid = bcrypt.checkpw(
            request.pin.encode('utf-8'),
            user.parental_pin_hash.encode('utf-8')
        )
    except Exception:
        valid = False
    
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid PIN"
        )
    
    return {"status": "verified"}


@router.post("/kids-mode")
async def toggle_kids_mode(
    request: UpdateModeRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Enable or disable kids mode."""
    user.kids_mode_enabled = request.enabled
    await db.commit()
    
    return {
        "kids_mode_enabled": user.kids_mode_enabled,
    }


@router.delete("/pin")
async def remove_parental_pin(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove parental control PIN."""
    user.parental_pin_hash = ""
    user.kids_mode_enabled = False
    await db.commit()
    
    return {"status": "pin_removed"}
