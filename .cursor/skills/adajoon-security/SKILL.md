---
name: adajoon-security
description: Enforce Adajoon security best practices including security headers (COOP, COEP, CSP), cookie attributes, JWT validation, CSRF protection, OAuth redirect validation, Stripe webhook signature verification, rate limiting, input validation, and secrets management. Use when working with authentication, cookies, security headers, sensitive data, API endpoints, webhooks, or user input handling.
---

# Adajoon Security Best Practices

**Version**: 1.0.0 (Updated: 2026-04-04)

Security patterns and requirements for the Adajoon streaming platform. All authentication, data handling, and API endpoints MUST follow these guidelines.

## Changelog
- v1.0.0 (2026-04-04): Initial versioning - established baseline security patterns

## 1. Security Headers

Apply comprehensive security headers via middleware. For OAuth compatibility, COOP/COEP must be permissive.

### Required Headers (All Environments)

```python
response.headers["Cross-Origin-Opener-Policy"] = "unsafe-none"  # Required for OAuth popups
response.headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"  # Required for OAuth
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-Frame-Options"] = "DENY"
response.headers["X-XSS-Protection"] = "1; mode=block"
response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
response.headers["Permissions-Policy"] = (
    "geolocation=(), microphone=(), camera=(), payment=(), usb=(), "
    "magnetometer=(), gyroscope=(), accelerometer=()"
)
```

### CSP (Production Only)

Content Security Policy with OAuth and streaming domain whitelisting:

```python
if settings.env == "production":
    csp_directives = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://accounts.google.com https://appleid.cdn-apple.com https://www.gstatic.com https://imasdk.googleapis.com",
        "style-src 'self' 'unsafe-inline' https://accounts.google.com https://appleid.cdn-apple.com https://fonts.googleapis.com",
        "img-src 'self' data: https:",
        "media-src 'self' blob: https:",
        "connect-src 'self' https://iptv-org.github.io https://de1.api.radio-browser.info https://raw.githubusercontent.com https://accounts.google.com https://appleid.apple.com https://fonts.googleapis.com https://fonts.gstatic.com https://imasdk.googleapis.com https://www.gstatic.com",
        "font-src 'self' data: https://fonts.gstatic.com",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self' https://accounts.google.com https://appleid.apple.com",
        "frame-src 'self' https://accounts.google.com https://appleid.apple.com",
        "frame-ancestors 'none'",
        "upgrade-insecure-requests",
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
```

**Adding new external domains:**
1. Only whitelist trusted domains
2. Use specific domains, not wildcards
3. Add to appropriate directive (script-src, connect-src, etc.)
4. Document the reason in code comments

### HSTS (Production Only)

```python
if settings.env == "production":
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
```

## 2. Cookie Security

All authentication cookies MUST use secure attributes.

### JWT Authentication Cookie

```python
def _set_auth_cookies(response: Response, user: User, token: str) -> None:
    cookie_domain = ".adajoon.com" if settings.env == "production" else None
    
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,      # XSS protection
        secure=True,        # HTTPS only
        samesite="lax",     # CSRF protection
        max_age=settings.jwt_expiry_days * 24 * 60 * 60,
        path="/",
        domain=cookie_domain,
    )
```

### CSRF Token Cookie

```python
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,     # Frontend needs to read this
        secure=True,
        samesite="lax",
        max_age=3600,       # 1 hour
        path="/",
        domain=cookie_domain,
    )
```

**Cookie Requirements:**
- `httponly=True` for sensitive tokens (prevents XSS)
- `secure=True` always (HTTPS only)
- `samesite="lax"` for CSRF protection
- `domain=".adajoon.com"` in production (supports www and non-www)
- `domain=None` in development/test

## 3. JWT Secret Management

JWT_SECRET is the most critical security configuration.

### Validation Rules

```python
def validate_config(self) -> None:
    errors = []
    
    if not self.jwt_secret:
        errors.append("JWT_SECRET environment variable must be set")
    elif len(self.jwt_secret) < 32:
        errors.append("JWT_SECRET must be at least 32 characters long")
    elif self.jwt_secret == "change-me-in-production":
        errors.append("JWT_SECRET must not be the default value")
    
    if errors:
        raise ValueError("Configuration validation failed")
```

### JWT Token Creation

```python
def create_token(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.jwt_expiry_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
```

**JWT Requirements:**
- Algorithm: HS256 (do not change without security review)
- Expiry: 30 days default
- Include only necessary claims (user_id, email, expiry)
- Never include passwords or sensitive data
- Always validate signature on decode

## 4. CSRF Protection

CSRF tokens required for all mutating operations (POST, PUT, DELETE, PATCH).

### Token Generation

```python
from itsdangerous import URLSafeTimedSerializer
import secrets

csrf_serializer = URLSafeTimedSerializer(settings.jwt_secret, salt="csrf-token")
CSRF_TOKEN_MAX_AGE = 3600  # 1 hour

def generate_csrf_token() -> str:
    random_string = secrets.token_urlsafe(32)
    return csrf_serializer.dumps(random_string)
```

### Token Validation

```python
async def verify_csrf_token(request: Request) -> None:
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    
    csrf_token = request.headers.get("X-CSRF-Token")
    if not csrf_token:
        raise HTTPException(status_code=403, detail="Missing CSRF token")
    
    try:
        csrf_serializer.loads(csrf_token, max_age=CSRF_TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        raise HTTPException(status_code=403, detail="Invalid or expired CSRF token")
```

### Using CSRF Protection

```python
@router.post("/favorites")
async def add_favorite(
    body: FavoriteRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token)  # Always add this dependency
):
    # Implementation
```

**CSRF Requirements:**
- Token must be 32 bytes (256 bits) minimum
- Use itsdangerous for signed tokens
- 1-hour expiry
- Check `X-CSRF-Token` header
- Skip for read-only methods (GET, HEAD, OPTIONS)
- Use same secret as JWT for consistency

## 5. OAuth Security

OAuth implementation must validate redirect URIs and verify tokens.

### Google OAuth

```python
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
    google_id = idinfo.get("sub", "")
    # Validate and create/update user
```

### Apple OAuth Redirect Validation

```python
@router.post("/apple/callback")
async def apple_callback(request: Request, response: Response):
    form = await request.form()
    id_token = form.get("id_token", "")
    origin = settings.webauthn_origin
    
    # Sanitize data for JavaScript embedding (XSS prevention)
    safe_id_token = json.dumps(id_token)
    safe_origin = json.dumps(origin)
    
    html_content = f"""<!DOCTYPE html>
<html><head><title>Signing in...</title></head>
<body><script>
try {{
  var data = {{ type:"apple-signin", idToken:{safe_id_token} }};
  if (window.opener) {{ 
    window.opener.postMessage(data, {safe_origin}); 
    window.close(); 
  }}
}} catch(e) {{ window.location.href = {safe_origin}; }}
</script></body></html>"""
    
    return HTMLResponse(content=html_content)
```

**OAuth Requirements:**
- Always verify tokens server-side
- Never trust client-provided tokens
- Use json.dumps() for embedding data in HTML (XSS prevention)
- Validate redirect URIs against whitelist
- Use postMessage with targetOrigin
- COOP must be "unsafe-none" for OAuth popups
- Rate limit OAuth endpoints

## 6. Stripe Webhook Signature Verification

Stripe webhooks MUST verify signatures to prevent forgery.

```python
@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    if not settings.stripe_webhook_secret:
        logger.error("Stripe webhook secret not configured")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        logger.error("Invalid webhook payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Process event
```

**Webhook Requirements:**
- Always use raw request body (before parsing)
- Check stripe-signature header exists
- Use stripe.Webhook.construct_event (handles verification)
- Log verification failures
- Return 400 for invalid signatures
- STRIPE_WEBHOOK_SECRET must be set in production

## 7. Rate Limiting

Use rate limiting on all authentication and public endpoints.

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/google")
@limiter.limit("10/minute")
async def google_login(request: Request, ...):
    pass
```

**Rate Limiting Guidelines:**
- Auth endpoints: 10/minute
- Public read endpoints: 100/minute
- Write endpoints: 30/minute
- Use IP-based limiting (get_remote_address)
- Apply before expensive operations
- Return 429 Too Many Requests on limit

## 8. Input Validation and Sanitization

Use Pydantic for all request bodies and strict validation.

### Pydantic Models

```python
from pydantic import BaseModel, Field

class FavoriteRequest(BaseModel):
    item_type: str = Field(..., max_length=10)
    item_id: str = Field(..., max_length=255)
    item_data: dict = {}

class VoteRequest(BaseModel):
    item_type: str = Field(max_length=10)
    item_id: str = Field(max_length=255)
    vote_type: str = Field(max_length=20)
```

### Validation Logic

```python
VALID_VOTE_TYPES = {"like", "dislike", "works", "broken", "slow", "bad_quality"}

@router.post("/votes")
async def submit_vote(req: VoteRequest, ...):
    if req.vote_type not in VALID_VOTE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid vote_type")
    if req.item_type not in ("tv", "radio"):
        raise HTTPException(status_code=400, detail="item_type must be 'tv' or 'radio'")
```

**Input Validation Requirements:**
- Use Pydantic Field() with max_length
- Validate against whitelists (not blacklists)
- Reject invalid data early
- Sanitize for SQL injection (use parameterized queries)
- Sanitize for XSS (use json.dumps for HTML embedding)
- Limit collection sizes (e.g., max 500 favorites)

## 9. Secrets Management

Never commit secrets. Use environment variables exclusively.

### Environment Variable Pattern

```python
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    jwt_secret: str = os.getenv("JWT_SECRET", "")
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    class Config:
        env_file = ".env"
```

### .gitignore Requirements

```gitignore
.env
.env.*
*.env
!.env.example
```

### Validation on Startup

```python
settings = Settings()
settings.validate_config()  # Fail fast if misconfigured
```

**Secrets Management Rules:**
- Never hardcode secrets
- Use .env files (git-ignored)
- Provide .env.example with dummy values
- Validate secrets on startup
- Use different secrets per environment
- Rotate secrets regularly (especially JWT_SECRET)
- Min 32 characters for cryptographic secrets
- Log warnings for missing optional secrets
- Fail startup for missing critical secrets in production

## 10. CORS Configuration

Configure CORS to allow only trusted origins.

```python
@property
def cors_origins(self) -> list[str]:
    cors_env = os.getenv("CORS_ORIGINS", "")
    if cors_env:
        return [origin.strip() for origin in cors_env.split(",") if origin.strip()]
    
    return [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://adajoon.com",
        "https://www.adajoon.com",
    ]
```

**CORS Requirements:**
- Whitelist specific origins (no wildcards in production)
- Use environment variable for configuration
- Include both www and non-www domains
- Include localhost for development
- Credentials: true (for cookies)
- Allowed methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
- Allowed headers: Content-Type, Authorization, X-CSRF-Token

## Security Checklist

When creating new endpoints or features:

- [ ] Security headers applied (via middleware)
- [ ] Authentication required (if not public)
- [ ] CSRF protection added (for mutations)
- [ ] Rate limiting applied
- [ ] Input validated with Pydantic
- [ ] Whitelist validation (not blacklist)
- [ ] SQL parameterized queries (no string concatenation)
- [ ] XSS prevention (json.dumps for HTML embedding)
- [ ] Secrets from environment variables
- [ ] Logging for security events
- [ ] Error messages don't leak sensitive info
- [ ] HTTPS enforced (secure cookies, HSTS)

## Common Vulnerabilities to Avoid

### SQL Injection

**Bad:**
```python
query = f"SELECT * FROM users WHERE email = '{email}'"
```

**Good:**
```python
result = await db.execute(select(User).where(User.email == email))
```

### XSS in OAuth Callback

**Bad:**
```python
html = f"<script>var token = '{id_token}';</script>"
```

**Good:**
```python
safe_token = json.dumps(id_token)
html = f"<script>var token = {safe_token};</script>"
```

### Missing CSRF on Mutations

**Bad:**
```python
@router.post("/delete-account")
async def delete_account(user: User = Depends(require_user)):
    pass
```

**Good:**
```python
@router.post("/delete-account")
async def delete_account(
    user: User = Depends(require_user),
    _csrf: None = Depends(verify_csrf_token)
):
    pass
```

### Weak JWT Secret

**Bad:**
```python
jwt_secret: str = "secret123"
```

**Good:**
```python
jwt_secret: str = os.getenv("JWT_SECRET", "")
# In .env: JWT_SECRET=<64+ character random string>
```

## Additional Resources

For detailed implementation examples, refer to:
- `backend/app/middleware/security_headers.py` - Header configuration
- `backend/app/routers/auth.py` - Cookie and JWT handling
- `backend/app/csrf.py` - CSRF implementation
- `backend/app/config.py` - Secrets validation
- `backend/app/routers/subscriptions.py` - Stripe webhook verification
