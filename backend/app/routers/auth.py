import json
import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from pydantic import BaseModel

from app.database import get_db
from app.config import settings
from app.models import User, UserFavorite

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


def create_token(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.jwt_expiry_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if not creds:
        return None
    try:
        payload = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def require_user(
    user: User | None = Depends(get_current_user),
) -> User:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


class GoogleTokenRequest(BaseModel):
    credential: str


class FavoriteRequest(BaseModel):
    item_type: str
    item_id: str
    item_data: dict = {}


@router.post("/google")
async def google_login(body: GoogleTokenRequest, db: AsyncSession = Depends(get_db)):
    try:
        idinfo = id_token.verify_oauth2_token(
            body.credential,
            google_requests.Request(),
            settings.google_client_id,
        )
    except Exception as e:
        logger.error("Google token verification failed: %s", e)
        raise HTTPException(status_code=400, detail="Invalid Google token")

    email = idinfo.get("email", "")
    name = idinfo.get("name", "")
    picture = idinfo.get("picture", "")
    google_id = idinfo.get("sub", "")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        user.name = name
        user.picture = picture
    else:
        user = User(
            email=email,
            name=name,
            picture=picture,
            provider="google",
            provider_id=google_id,
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    token = create_token(user.id, user.email)
    return {
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
        },
    }


@router.get("/me")
async def get_me(user: User = Depends(require_user)):
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
    }


@router.get("/favorites")
async def get_favorites(user: User = Depends(require_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserFavorite).where(UserFavorite.user_id == user.id)
    )
    favs = result.scalars().all()
    return [
        {
            "item_type": f.item_type,
            "item_id": f.item_id,
            "item_data": json.loads(f.item_data) if f.item_data else {},
        }
        for f in favs
    ]


@router.post("/favorites")
async def add_favorite(body: FavoriteRequest, user: User = Depends(require_user), db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(UserFavorite).where(
            UserFavorite.user_id == user.id,
            UserFavorite.item_type == body.item_type,
            UserFavorite.item_id == body.item_id,
        )
    )
    if existing.scalar_one_or_none():
        return {"status": "already_exists"}

    fav = UserFavorite(
        user_id=user.id,
        item_type=body.item_type,
        item_id=body.item_id,
        item_data=json.dumps(body.item_data),
    )
    db.add(fav)
    await db.commit()
    return {"status": "added"}


@router.delete("/favorites/{item_type}/{item_id}")
async def remove_favorite(item_type: str, item_id: str, user: User = Depends(require_user), db: AsyncSession = Depends(get_db)):
    await db.execute(
        delete(UserFavorite).where(
            UserFavorite.user_id == user.id,
            UserFavorite.item_type == item_type,
            UserFavorite.item_id == item_id,
        )
    )
    await db.commit()
    return {"status": "removed"}


@router.post("/favorites/sync")
async def sync_favorites(favorites: list[FavoriteRequest], user: User = Depends(require_user), db: AsyncSession = Depends(get_db)):
    """Bulk sync: merge client-side favorites into server. Used on first login."""
    for fav in favorites:
        existing = await db.execute(
            select(UserFavorite).where(
                UserFavorite.user_id == user.id,
                UserFavorite.item_type == fav.item_type,
                UserFavorite.item_id == fav.item_id,
            )
        )
        if not existing.scalar_one_or_none():
            db.add(UserFavorite(
                user_id=user.id,
                item_type=fav.item_type,
                item_id=fav.item_id,
                item_data=json.dumps(fav.item_data),
            ))
    await db.commit()

    result = await db.execute(
        select(UserFavorite).where(UserFavorite.user_id == user.id)
    )
    favs = result.scalars().all()
    return [
        {
            "item_type": f.item_type,
            "item_id": f.item_id,
            "item_data": json.loads(f.item_data) if f.item_data else {},
        }
        for f in favs
    ]
