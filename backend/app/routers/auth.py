import json
import base64
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
import requests as http_requests

from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    UserVerificationRequirement,
    PublicKeyCredentialDescriptor,
    AuthenticatorTransport,
)
from webauthn.helpers import bytes_to_base64url, base64url_to_bytes

from app.database import get_db
from app.config import settings
from app.models import User, UserFavorite, Passkey

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)

APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"

# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_token(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.jwt_expiry_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_challenge_token(challenge: bytes) -> str:
    payload = {
        "ch": base64.urlsafe_b64encode(challenge).decode("ascii"),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=3),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_challenge_token(token: str) -> bytes:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    return base64.urlsafe_b64decode(payload["ch"])


def _user_response(user: User, token: str) -> dict:
    return {
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
        },
    }


# ---------------------------------------------------------------------------
# Auth dependencies
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class GoogleTokenRequest(BaseModel):
    credential: str

class AppleTokenRequest(BaseModel):
    id_token: str
    user_name: str = ""

class FavoriteRequest(BaseModel):
    item_type: str
    item_id: str
    item_data: dict = {}

class PasskeyRegisterBody(BaseModel):
    credential: dict
    challenge_token: str
    name: str = "Passkey"

class PasskeyLoginBody(BaseModel):
    credential: dict
    challenge_token: str


# ===========================================================================
# GOOGLE SIGN-IN
# ===========================================================================

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
        user = User(email=email, name=name, picture=picture, provider="google", provider_id=google_id)
        db.add(user)

    await db.commit()
    await db.refresh(user)
    return _user_response(user, create_token(user.id, user.email))


# ===========================================================================
# APPLE SIGN-IN
# ===========================================================================

def _verify_apple_identity_token(identity_token: str) -> dict:
    keys_resp = http_requests.get(APPLE_KEYS_URL, timeout=10)
    apple_keys = keys_resp.json()["keys"]
    header = jwt.get_unverified_header(identity_token)
    kid = header.get("kid")
    key = next((k for k in apple_keys if k["kid"] == kid), None)
    if not key:
        raise ValueError("Apple public key not found for kid: " + str(kid))

    payload = jwt.decode(
        identity_token,
        key,
        algorithms=["RS256"],
        audience=settings.apple_client_id,
        issuer=APPLE_ISSUER,
    )
    return payload


@router.post("/apple")
async def apple_login(body: AppleTokenRequest, db: AsyncSession = Depends(get_db)):
    if not settings.apple_client_id:
        raise HTTPException(status_code=501, detail="Apple Sign-In not configured")

    try:
        payload = _verify_apple_identity_token(body.id_token)
    except Exception as e:
        logger.error("Apple token verification failed: %s", e)
        raise HTTPException(status_code=400, detail="Invalid Apple token")

    apple_id = payload.get("sub", "")
    email = payload.get("email", "")
    name = body.user_name or email.split("@")[0]

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        if body.user_name:
            user.name = body.user_name
    else:
        user = User(email=email, name=name, picture="", provider="apple", provider_id=apple_id)
        db.add(user)

    await db.commit()
    await db.refresh(user)
    return _user_response(user, create_token(user.id, user.email))


# ===========================================================================
# PASSKEY / WEBAUTHN
# ===========================================================================

@router.post("/passkey/register-options")
async def passkey_register_options(user: User = Depends(require_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Passkey).where(Passkey.user_id == user.id))
    existing = result.scalars().all()

    exclude = [
        PublicKeyCredentialDescriptor(
            id=base64url_to_bytes(pk.credential_id),
            transports=[AuthenticatorTransport(t) for t in json.loads(pk.transports or "[]") if t],
        )
        for pk in existing
    ]

    options = generate_registration_options(
        rp_id=settings.webauthn_rp_id,
        rp_name=settings.webauthn_rp_name,
        user_id=str(user.id).encode("utf-8"),
        user_name=user.email,
        user_display_name=user.name or user.email,
        exclude_credentials=exclude,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
    )

    challenge_token = create_challenge_token(options.challenge)
    return {
        "options": json.loads(options_to_json(options)),
        "challenge_token": challenge_token,
    }


@router.post("/passkey/register")
async def passkey_register(body: PasskeyRegisterBody, user: User = Depends(require_user), db: AsyncSession = Depends(get_db)):
    try:
        expected_challenge = decode_challenge_token(body.challenge_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired challenge")

    try:
        verification = verify_registration_response(
            credential=body.credential,
            expected_challenge=expected_challenge,
            expected_rp_id=settings.webauthn_rp_id,
            expected_origin=settings.webauthn_origin,
        )
    except Exception as e:
        logger.error("Passkey registration verification failed: %s", e)
        raise HTTPException(status_code=400, detail="Registration verification failed")

    cred_id_b64 = bytes_to_base64url(verification.credential_id)
    pub_key_b64 = bytes_to_base64url(verification.credential_public_key)

    transports = []
    if body.credential.get("response", {}).get("transports"):
        transports = body.credential["response"]["transports"]

    passkey = Passkey(
        user_id=user.id,
        credential_id=cred_id_b64,
        public_key=pub_key_b64,
        sign_count=verification.sign_count,
        transports=json.dumps(transports),
        name=body.name or "Passkey",
    )
    db.add(passkey)
    await db.commit()
    return {"status": "registered", "name": passkey.name}


@router.post("/passkey/login-options")
async def passkey_login_options():
    options = generate_authentication_options(
        rp_id=settings.webauthn_rp_id,
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    challenge_token = create_challenge_token(options.challenge)
    return {
        "options": json.loads(options_to_json(options)),
        "challenge_token": challenge_token,
    }


@router.post("/passkey/login")
async def passkey_login(body: PasskeyLoginBody, db: AsyncSession = Depends(get_db)):
    try:
        expected_challenge = decode_challenge_token(body.challenge_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired challenge")

    cred_response = body.credential
    cred_id_b64 = cred_response.get("id", "")

    result = await db.execute(select(Passkey).where(Passkey.credential_id == cred_id_b64))
    passkey = result.scalar_one_or_none()
    if not passkey:
        raise HTTPException(status_code=400, detail="Passkey not found")

    try:
        verification = verify_authentication_response(
            credential=cred_response,
            expected_challenge=expected_challenge,
            expected_rp_id=settings.webauthn_rp_id,
            expected_origin=settings.webauthn_origin,
            credential_public_key=base64url_to_bytes(passkey.public_key),
            credential_current_sign_count=passkey.sign_count,
        )
    except Exception as e:
        logger.error("Passkey login verification failed: %s", e)
        raise HTTPException(status_code=400, detail="Authentication verification failed")

    passkey.sign_count = verification.new_sign_count
    await db.commit()

    user_result = await db.execute(select(User).where(User.id == passkey.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    return _user_response(user, create_token(user.id, user.email))


@router.get("/passkeys")
async def list_passkeys(user: User = Depends(require_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Passkey).where(Passkey.user_id == user.id))
    passkeys = result.scalars().all()
    return [
        {"id": pk.id, "name": pk.name, "created_at": str(pk.created_at)}
        for pk in passkeys
    ]


# ===========================================================================
# USER PROFILE
# ===========================================================================

@router.get("/me")
async def get_me(user: User = Depends(require_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Passkey).where(Passkey.user_id == user.id))
    has_passkey = result.first() is not None
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "has_passkey": has_passkey,
    }


# ===========================================================================
# FAVORITES
# ===========================================================================

@router.get("/favorites")
async def get_favorites(user: User = Depends(require_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserFavorite).where(UserFavorite.user_id == user.id))
    favs = result.scalars().all()
    return [
        {"item_type": f.item_type, "item_id": f.item_id, "item_data": json.loads(f.item_data) if f.item_data else {}}
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

    fav = UserFavorite(user_id=user.id, item_type=body.item_type, item_id=body.item_id, item_data=json.dumps(body.item_data))
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
                user_id=user.id, item_type=fav.item_type, item_id=fav.item_id, item_data=json.dumps(fav.item_data),
            ))
    await db.commit()

    result = await db.execute(select(UserFavorite).where(UserFavorite.user_id == user.id))
    favs = result.scalars().all()
    return [
        {"item_type": f.item_type, "item_id": f.item_id, "item_data": json.loads(f.item_data) if f.item_data else {}}
        for f in favs
    ]
