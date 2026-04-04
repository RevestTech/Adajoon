import asyncio
import json
import base64
import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select, delete, exists, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from jose import jwt, JWTError
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from pydantic import BaseModel, Field
import httpx

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
from app.models import User, UserFavorite, UserVote, Passkey
from app.csrf import generate_csrf_token, verify_csrf_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)
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


def _set_auth_cookies(response: Response, user: User, token: str) -> None:
    """Set authentication cookies (httpOnly JWT + CSRF token)."""
    # Determine cookie domain - use adajoon.com for both www and non-www
    cookie_domain = ".adajoon.com" if settings.env == "production" else None
    
    # Set JWT in httpOnly cookie (XSS-safe)
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        secure=True,  # HTTPS only in production
        samesite="lax",
        max_age=settings.jwt_expiry_days * 24 * 60 * 60,
        path="/",
        domain=cookie_domain,
    )
    
    # Set CSRF token in readable cookie for frontend
    csrf_token = generate_csrf_token()
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,  # Frontend needs to read this
        secure=True,
        samesite="lax",
        max_age=3600,  # 1 hour
        path="/",
        domain=cookie_domain,
    )


def _user_response(user: User) -> dict:
    """Return user data (no token in body - it's in cookies)."""
    return {
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
    auth_token: str | None = Cookie(default=None),
    creds: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    # Try cookie first (new auth method), then fall back to header (legacy)
    token = auth_token or (creds.credentials if creds else None)
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
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
    item_type: str = Field(..., max_length=10)
    item_id: str = Field(..., max_length=255)
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
@limiter.limit("10/minute")
async def google_login(request: Request, response: Response, body: GoogleTokenRequest, db: AsyncSession = Depends(get_db)):
    try:
        idinfo = await asyncio.to_thread(
            id_token.verify_oauth2_token,
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
    token = create_token(user.id, user.email)
    _set_auth_cookies(response, user, token)
    return _user_response(user)


# ===========================================================================
# APPLE SIGN-IN
# ===========================================================================

from app.redis_client import cache_get, cache_set

APPLE_KEYS_TTL = 3600  # 1 hour

async def _get_apple_keys() -> list:
    """Fetch Apple JWKS with Redis caching (1 hour TTL)."""
    cached = await cache_get("apple_public_keys")
    if cached:
        return cached
    
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(APPLE_KEYS_URL)
        resp.raise_for_status()
        keys = resp.json()["keys"]
    
    await cache_set("apple_public_keys", keys, APPLE_KEYS_TTL)
    return keys


async def _verify_apple_identity_token(identity_token: str) -> dict:
    apple_keys = await _get_apple_keys()
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


@router.post("/apple/callback")
async def apple_callback(request: Request, response: Response):
    """Apple redirects here with a form POST. We relay the data to the opener window."""
    form = await request.form()
    id_token = form.get("id_token", "")
    user_raw = form.get("user", "")
    origin = settings.webauthn_origin
    
    # Safely encode data for JavaScript embedding (XSS prevention)
    safe_id_token = json.dumps(id_token)
    safe_user_data = "null"
    if user_raw:
        try:
            # Validate and re-serialize to ensure proper escaping
            parsed = json.loads(user_raw)
            safe_user_data = json.dumps(parsed)
        except (json.JSONDecodeError, ValueError):
            safe_user_data = "null"
    safe_origin = json.dumps(origin)
    
    # Set COOP header to allow popup communication
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
    
    html_content = f"""<!DOCTYPE html><html><head><title>Signing in...</title></head>
<body><p>Completing sign-in...</p><script>
try {{
  var data = {{ type:"apple-signin", idToken:{safe_id_token}, userData:{safe_user_data} }};
  if (window.opener) {{ window.opener.postMessage(data, {safe_origin}); window.close(); }}
  else {{ window.location.href = {safe_origin}; }}
}} catch(e) {{ window.location.href = {safe_origin}; }}
</script></body></html>"""
    
    return HTMLResponse(content=html_content, headers=dict(response.headers))


@router.post("/apple")
@limiter.limit("10/minute")
async def apple_login(request: Request, response: Response, body: AppleTokenRequest, db: AsyncSession = Depends(get_db)):
    if not settings.apple_client_id:
        raise HTTPException(status_code=501, detail="Apple Sign-In not configured")

    try:
        payload = await _verify_apple_identity_token(body.id_token)
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
    token = create_token(user.id, user.email)
    _set_auth_cookies(response, user, token)
    return _user_response(user)


# ===========================================================================
# PASSKEY / WEBAUTHN
# ===========================================================================

@router.post("/passkey/register-options")
@limiter.limit("10/minute")
async def passkey_register_options(
    request: Request,user: User = Depends(require_user), db: AsyncSession = Depends(get_db)):
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
async def passkey_login(body: PasskeyLoginBody, response: Response, db: AsyncSession = Depends(get_db)):
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

    token = create_token(user.id, user.email)
    _set_auth_cookies(response, user, token)
    return _user_response(user)


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
    has_passkey = (await db.execute(
        select(exists().where(Passkey.user_id == user.id))
    )).scalar()
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "has_passkey": bool(has_passkey),
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
async def add_favorite(
    body: FavoriteRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token)
):
    stmt = pg_insert(UserFavorite).values(
        user_id=user.id, item_type=body.item_type,
        item_id=body.item_id, item_data=json.dumps(body.item_data),
    ).on_conflict_do_nothing(index_elements=["user_id", "item_type", "item_id"])
    result = await db.execute(stmt)
    await db.commit()
    return {"status": "added" if result.rowcount else "already_exists"}


@router.delete("/favorites/{item_type}/{item_id}")
async def remove_favorite(
    item_type: str,
    item_id: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token)
):
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
async def sync_favorites(
    favorites: list[FavoriteRequest],
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token)
):
    if len(favorites) > 500:
        raise HTTPException(status_code=400, detail="Too many favorites (max 500)")
    for fav in favorites:
        stmt = pg_insert(UserFavorite).values(
            user_id=user.id, item_type=fav.item_type,
            item_id=fav.item_id, item_data=json.dumps(fav.item_data),
        ).on_conflict_do_nothing(index_elements=["user_id", "item_type", "item_id"])
        await db.execute(stmt)
    await db.commit()

    result = await db.execute(select(UserFavorite).where(UserFavorite.user_id == user.id))
    favs = result.scalars().all()
    return [
        {"item_type": f.item_type, "item_id": f.item_id, "item_data": json.loads(f.item_data) if f.item_data else {}}
        for f in favs
    ]


# ---------------------------------------------------------------------------
# Voting / Feedback
# ---------------------------------------------------------------------------

VALID_VOTE_TYPES = {"like", "dislike", "works", "broken", "slow", "bad_quality"}


class VoteRequest(BaseModel):
    item_type: str = Field(max_length=10)
    item_id: str = Field(max_length=255)
    vote_type: str = Field(max_length=20)


@router.post("/votes")
async def submit_vote(
    req: VoteRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token)
):
    if req.vote_type not in VALID_VOTE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid vote_type. Must be one of: {', '.join(sorted(VALID_VOTE_TYPES))}")
    if req.item_type not in ("tv", "radio"):
        raise HTTPException(status_code=400, detail="item_type must be 'tv' or 'radio'")

    existing = await db.execute(
        select(UserVote).where(
            UserVote.user_id == user.id,
            UserVote.item_type == req.item_type,
            UserVote.item_id == req.item_id,
            UserVote.vote_type == req.vote_type,
        )
    )
    if existing.scalar_one_or_none():
        await db.execute(
            delete(UserVote).where(
                UserVote.user_id == user.id,
                UserVote.item_type == req.item_type,
                UserVote.item_id == req.item_id,
                UserVote.vote_type == req.vote_type,
            )
        )
        await db.commit()
        return {"status": "removed", "vote_type": req.vote_type}

    stmt = pg_insert(UserVote).values(
        user_id=user.id,
        item_type=req.item_type,
        item_id=req.item_id,
        vote_type=req.vote_type,
    ).on_conflict_do_nothing()
    await db.execute(stmt)
    await db.commit()
    return {"status": "added", "vote_type": req.vote_type}


@router.get("/votes/me")
async def get_my_votes(item_type: str, user: User = Depends(require_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserVote.item_id, UserVote.vote_type).where(
            UserVote.user_id == user.id,
            UserVote.item_type == item_type,
        )
    )
    votes = {}
    for item_id, vote_type in result:
        votes.setdefault(item_id, []).append(vote_type)
    return votes


@router.get("/votes/summary")
async def get_vote_summary(item_type: str, item_ids: str, db: AsyncSession = Depends(get_db)):
    """Public endpoint — returns aggregate vote counts for a batch of items."""
    ids = [i.strip() for i in item_ids.split(",") if i.strip()][:100]
    if not ids:
        return {}

    result = await db.execute(
        select(
            UserVote.item_id,
            UserVote.vote_type,
            func.count().label("cnt"),
        )
        .where(UserVote.item_type == item_type, UserVote.item_id.in_(ids))
        .group_by(UserVote.item_id, UserVote.vote_type)
    )

    summary = {}
    for item_id, vote_type, cnt in result:
        summary.setdefault(item_id, {})[vote_type] = cnt
    return summary
