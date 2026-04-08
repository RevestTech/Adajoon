# Adajoon Skills Reference for Claude Conversations

This comprehensive guide consolidates all Adajoon coding skills for use in direct Claude conversations. Reference this file with `@CLAUDE.md` when you need project-specific guidance.

**Quick Jump**:
- [Backend (FastAPI)](#backend-fastapi)
- [Frontend (React)](#frontend-react)
- [Security](#security)
- [Database](#database)
- [Deployment](#deployment)
- [Conventions](#conventions)
- [Skill Improvement](#skill-improvement)
- [Common Scenarios](#common-scenarios)

---

## Project Overview

**Adajoon** is a streaming TV/radio platform built with:

### Stack
- **Backend**: Python 3.12, FastAPI, SQLAlchemy (async), PostgreSQL, Redis
- **Frontend**: React 18, Vite, OAuth (Google/Apple)
- **Auth**: Cookie-based JWT with CSRF protection
- **Deployment**: Railway (dual-service architecture)

### Architecture (Updated 2026-04-07)
```
Railway Project: Adajoon (production)
├── Redis         (cache + sessions, with volume)
├── Postgres      (primary DB, with volume)
├── frontend      (nginx → React SPA)
│   ├── Public: adajoon-production.up.railway.app
│   ├── Proxies /api/* → backend.railway.internal:8080
│   ├── Server-side 301 redirect: adajoon.com → www.adajoon.com
│   └── Aggressive no-cache headers on index.html (all location contexts)
├── backend       (FastAPI/Uvicorn)
│   ├── Public: adajoon.com / www.adajoon.com
│   ├── Handles /api/* routes
│   └── Proxies / → frontend (internal)
└── worker        (background tasks)
```

**Two public entry points:**
1. `www.adajoon.com` → Backend (handles API + proxies frontend)
2. `adajoon-production.up.railway.app` → Frontend (serves SPA + proxies API to backend)

**Critical**: Service-to-service communication uses Railway private networking on port **8080** (not 8000). Example: `http://backend.railway.internal:8080`

### iOS Safari / Mobile Compatibility (Added 2026-04-07)
- **CSS heights**: Use `100vh` fallback before `100dvh` — never use `-webkit-fill-available` on height (can compute to 0 on iOS)
- **External scripts**: Always load third-party SDKs (Chromecast, IMA, etc.) with `async defer` — sync scripts block iOS Safari parser
- **Nginx caching**: `location = /index.html` no-cache headers do NOT apply when `try_files` serves from `location /` — must add no-cache to catch-all block
- **Diagnostics**: `index.html` includes inline loading fallback and `window.onerror` handler for visible error reporting

---

## Backend (FastAPI)

### Full Reference
👉 [adajoon-backend/SKILL.md](./adajoon-backend/SKILL.md)

### Key Patterns

#### Router Structure
```python
import logging
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.auth import require_user
from app.csrf import verify_csrf_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/feature", tags=["feature"])
```

**Rules**:
- Always use `/api/` prefix
- Module-level logger with `logging.getLogger(__name__)`
- Tags match feature name

#### Authentication
```python
# Optional auth (returns None if not authenticated)
@router.get("/endpoint")
async def optional(user: User | None = Depends(get_current_user)):
    pass

# Required auth (raises 401 if not authenticated)
@router.post("/protected")
async def protected(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token)  # Always add for mutations
):
    pass
```

#### CSRF Protection
**CRITICAL**: Apply to ALL mutating endpoints (POST/PUT/PATCH/DELETE)

```python
from app.csrf import verify_csrf_token

@router.post("/favorites")
async def add_favorite(
    body: Request,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token)  # Last parameter
):
    pass
```

#### Caching
```python
from app.redis_client import cache_get, cache_set, cache_delete

CACHE_TTL = 300  # 5 minutes

@router.get("/data")
async def get_data(db: AsyncSession = Depends(get_db)):
    cached = await cache_get("key")
    if cached:
        return cached
    
    data = await fetch_from_db(db)
    await cache_set("key", data, CACHE_TTL)
    return data

@router.post("/data")
async def create_data(...):
    result = await create_item(db)
    await cache_delete("key")  # Invalidate
    return result
```

#### Error Handling
```python
from fastapi import status

try:
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input"
        )
    result = await operation(db)
    return result
except HTTPException:
    raise  # Re-raise HTTPExceptions
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e)
    )
```

### Quick Checklist
- [ ] Router uses `/api/` prefix
- [ ] Module-level logger defined
- [ ] Authentication dependency added
- [ ] CSRF protection on mutations
- [ ] Caching on read-heavy endpoints
- [ ] Cache invalidation on mutations
- [ ] Type hints on all functions
- [ ] Structured logging with context

---

## Frontend (React)

### Full Reference
👉 [adajoon-frontend/SKILL.md](./adajoon-frontend/SKILL.md)

### Key Patterns

#### API Client
```javascript
import { authenticatedFetch } from '../utils/csrf';

const BASE = '/api';

// GET requests (public data)
export async function fetchData() {
  const res = await fetch(`${BASE}/endpoint`);
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
}

// Mutations (POST/PUT/DELETE) - ALWAYS use authenticatedFetch
export async function createItem(data) {
  const res = await authenticatedFetch(`${BASE}/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to create');
  return res.json();
}
```

**CRITICAL**: `authenticatedFetch` automatically handles CSRF tokens. Never manually add `X-CSRF-Token` header.

#### Custom Hooks Pattern
```javascript
import { createContext, useContext, useState, useCallback, useMemo } from 'react';

const MyContext = createContext(null);

export function MyProvider({ children }) {
  const [state, setState] = useState(null);
  const [loading, setLoading] = useState(false);

  const performAction = useCallback(async () => {
    setLoading(true);
    try {
      // action logic
    } finally {
      setLoading(false);  // Always clear loading
    }
  }, []);

  const value = useMemo(() => ({
    state,
    loading,
    performAction
  }), [state, loading, performAction]);

  return <MyContext.Provider value={value}>{children}</MyContext.Provider>;
}

export function useMyHook() {
  return useContext(MyContext);
}
```

**Rules**:
- Export both Provider and hook
- Use `useCallback` for functions
- Use `useMemo` for context value
- Always include loading state
- Use `try/finally` for loading cleanup

#### Loading States
```javascript
const [loading, setLoading] = useState(false);
const [error, setError] = useState('');

const handleAction = async () => {
  setError('');
  setLoading(true);
  try {
    await someAsyncAction();
  } catch (err) {
    setError('Action failed. Please try again.');
  } finally {
    setLoading(false);
  }
};

return (
  <>
    {error && <div className="error">{error}</div>}
    <button onClick={handleAction} disabled={loading}>
      {loading ? 'Processing...' : 'Submit'}
    </button>
  </>
);
```

### Quick Checklist
- [ ] Using `authenticatedFetch` for mutations
- [ ] Loading states for async operations
- [ ] Error handling with user feedback
- [ ] `try/finally` for loading cleanup
- [ ] Context + Provider + hook pattern
- [ ] `useCallback`/`useMemo` for performance
- [ ] Environment variables via `import.meta.env.VITE_*`

---

## Security

### Full Reference
👉 [adajoon-security/SKILL.md](./adajoon-security/SKILL.md)

### Critical Patterns

#### Security Headers
Applied via middleware in production:
```python
response.headers["Cross-Origin-Opener-Policy"] = "unsafe-none"  # OAuth popups
response.headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-Frame-Options"] = "DENY"
response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

if settings.env == "production":
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "..."
```

#### Cookie Security
```python
def _set_auth_cookies(response: Response, user: User, token: str):
    cookie_domain = ".adajoon.com" if settings.env == "production" else None
    
    # JWT token (httpOnly - prevents XSS)
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,   # XSS protection
        secure=True,     # HTTPS only
        samesite="lax",  # CSRF protection
        max_age=settings.jwt_expiry_days * 24 * 60 * 60,
        path="/",
        domain=cookie_domain
    )
    
    # CSRF token (not httpOnly - frontend needs to read)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,  # Frontend reads this
        secure=True,
        samesite="lax",
        max_age=3600,
        path="/",
        domain=cookie_domain
    )
```

#### JWT Validation
```python
def validate_config(self):
    errors = []
    if not self.jwt_secret:
        errors.append("JWT_SECRET must be set")
    elif len(self.jwt_secret) < 32:
        errors.append("JWT_SECRET must be at least 32 characters")
    elif self.jwt_secret == "change-me-in-production":
        errors.append("JWT_SECRET must not be default value")
    if errors:
        raise ValueError("Configuration validation failed")
```

#### Input Validation
```python
from pydantic import BaseModel, Field

class ItemRequest(BaseModel):
    item_type: str = Field(..., max_length=10)
    item_id: str = Field(..., max_length=255)

VALID_TYPES = {"tv", "radio"}

@router.post("/items")
async def create_item(req: ItemRequest, ...):
    if req.item_type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail="Invalid item_type")
    # Process...
```

#### Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/auth/login")
@limiter.limit("10/minute")
async def login(request: Request, ...):
    pass
```

### Security Checklist
- [ ] Security headers applied (via middleware)
- [ ] Cookies: `httponly=True, secure=True, samesite="lax"`
- [ ] JWT secret validated (32+ chars)
- [ ] CSRF protection on mutations
- [ ] Input validation with Pydantic
- [ ] Rate limiting on auth endpoints
- [ ] No secrets in code (use env vars)
- [ ] SQL parameterized queries
- [ ] XSS prevention (json.dumps for HTML)

---

## Database

### Full Reference
👉 [adajoon-database/SKILL.md](./adajoon-database/SKILL.md)

### Critical Rules

**NEVER** manually create tables with `Base.metadata.create_all()`. **ALWAYS** use Alembic migrations.

#### Model Patterns
```python
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, func
from app.database import Base

class Model(Base):
    __tablename__ = "table_name"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), 
                     nullable=False, index=True)
    
    # ALWAYS use DateTime(timezone=True), NEVER strings
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), 
                       server_default=func.now(), onupdate=func.now())
```

#### Migration Template
```python
"""Brief description

Revision ID: 001
Revises: None
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None

def upgrade() -> None:
    op.execute('''
        CREATE TABLE IF NOT EXISTS table_name (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    ''')
    
    op.execute('CREATE INDEX IF NOT EXISTS ix_table_user_id ON table_name (user_id);')

def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS table_name;')
```

**Rules**:
- Use `IF NOT EXISTS` / `IF EXISTS` for idempotency
- Always implement downgrade
- Sequential 3-digit revision IDs
- Index all foreign keys

#### Query Patterns
```python
from sqlalchemy import select

# Select
result = await db.execute(select(User).where(User.id == user_id))
user = result.scalar_one_or_none()

# Insert
db.add(User(email="user@example.com"))
await db.commit()
await db.refresh(user)

# Update
user.name = "New Name"
await db.commit()

# Delete
await db.delete(user)
await db.commit()
```

### Database Checklist
- [ ] Using Alembic migrations (not manual schema)
- [ ] Timestamps use `DateTime(timezone=True)`
- [ ] Foreign keys indexed
- [ ] Migrations use `IF NOT EXISTS`
- [ ] Downgrade implemented
- [ ] Async/await for all queries

---

## Deployment

### Full Reference
👉 [adajoon-deployment/SKILL.md](./adajoon-deployment/SKILL.md)

### Railway Architecture

**Dual-Service Pattern**:
1. **Backend** (FastAPI) - Public domain, handles API + proxies frontend
2. **Frontend** (React/Nginx) - Internal only, accessed via backend proxy

**Why?**
- Security headers applied by backend middleware
- Single public domain simplifies SSL/DNS
- Centralized logging and rate limiting

#### Environment Variables

**Backend**:
```bash
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
FRONTEND_URL=https://frontend-production-xyz.up.railway.app  # Internal
JWT_SECRET=<64+ character random string>
JSON_LOGS=true  # Production
LOG_LEVEL=INFO
CORS_ORIGINS=["https://adajoon.com"]
```

**Frontend**:
```bash
BACKEND_URL=https://backend-production-xyz.up.railway.app  # Internal
PORT=80
```

**⚠️ Critical**: When deploying multiple Python services (backend, worker), ensure ALL have shared env vars:
- `JWT_SECRET` (same across all services)
- `DATABASE_URL`
- `REDIS_URL`
- `ENVIRONMENT`

#### Docker Multi-Stage Build (Backend)
```dockerfile
# Stage 1: Builder
FROM python:3.12-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt && \
    rm -rf /wheels
COPY . .
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s CMD \
  python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health').read()" || exit 1
CMD ["./start.sh"]
```

#### Start Script (backend/start.sh)
```bash
#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Deployment Workflow (How We Deploy)

**Railway CLI** is installed at `/opt/homebrew/bin/railway` and authenticated as `khash@khash.com`.

```bash
# Check status
cd ~/Projects/Adajoon
railway status                    # Shows linked project/service
railway deployment list           # Recent deployments with status

# Deploy frontend (from frontend directory)
cd frontend
railway service frontend          # Link to frontend service
railway up --detach               # Upload and deploy, returns immediately

# Deploy backend
cd ..
railway service backend
railway up --detach
```

**Git-triggered deploys**: Pushing to `main` on GitHub can also trigger Railway auto-deploy (if configured for the service). Use `railway up` for manual/immediate deploys.

**Railway GraphQL API** (`https://backboard.railway.app/graphql/v2`): Used for service management (rename, delete, query). Requires Bearer token from `~/.config/railway/config.json` or Railway CLI auth.

### Deployment Checklist
- [ ] Migrations tested locally
- [ ] Environment variables set (especially `JWT_SECRET`)
- [ ] `FRONTEND_URL` / `BACKEND_URL` configured
- [ ] `JSON_LOGS=true` for production
- [ ] Health checks return 200
- [ ] Frontend NOT publicly exposed
- [ ] Multi-stage Docker builds
- [ ] Migrations run in start.sh

---

## Conventions

### Full Reference
👉 [adajoon-conventions/SKILL.md](./adajoon-conventions/SKILL.md)

### Python Standards

**Type Hints** (Required)
```python
async def search(db: AsyncSession, query: str) -> tuple[list[Channel], int]:
    channels, total = await get_data(db)
    return channels, total

def create_token(user_id: int) -> str:
    return jwt.encode(payload, secret)

# Use modern syntax
async def get_user(auth_token: str | None) -> User | None:
    pass  # Not Optional[User]
```

**Imports**
```python
# Standard library
import asyncio
import logging
from datetime import datetime

# Third-party
from fastapi import APIRouter
from sqlalchemy import select

# Local
from app.database import get_db
from app.models import User
```

**Naming**
```python
# snake_case for functions/variables
async def get_user_profile():
    user_id = 123

# PascalCase for classes
class UserProfile(BaseModel):
    pass

# UPPER_SNAKE_CASE for constants
CACHE_TTL = 300
VALID_TYPES = {"tv", "radio"}
```

**Comments**
```python
# ❌ BAD - obvious
# Get the user from the database
user = await get_user(db, user_id)

# ✅ GOOD - explains non-obvious constraint
SYNC_API_KEY = os.getenv("SYNC_API_KEY", "")  # Empty by default to disable endpoint

# ✅ GOOD - explains security consideration
# Constant-time comparison to prevent timing attacks
if not secrets.compare_digest(x_sync_key, SYNC_API_KEY):
    raise HTTPException(status_code=403)
```

### JavaScript Standards

**Variables**
```javascript
const user = await fetchUser();  // Default to const
let count = 0;                   // Use let when reassignment needed
// NEVER use var
```

**Functions**
```javascript
const handleClick = () => {
  console.log('clicked');
};

const fetchData = async () => {
  const res = await fetch(url);
  return res.json();
};
```

**Naming**
```javascript
const userName = "John";           // camelCase
const API_BASE = "/api";           // UPPER_SNAKE_CASE

function ChannelGrid({ channels }) {  // PascalCase for components
  return <div>...</div>;
}

function useAuth() {               // Hooks start with 'use'
  return { user };
}
```

### Git Commits

Use Conventional Commits:
```
feat(auth): add passkey registration flow
fix(api): correct pagination calculation
refactor(frontend): extract channel components
docs: update API documentation
chore(deps): upgrade fastapi to 0.109.0
```

### Conventions Checklist
- [ ] Type hints on all Python functions
- [ ] Modern union syntax (`str | None`)
- [ ] f-strings for formatting
- [ ] Imports organized (stdlib, third-party, local)
- [ ] snake_case/PascalCase naming
- [ ] const/let (no var) in JavaScript
- [ ] Arrow functions
- [ ] No obvious comments
- [ ] Conventional commit messages

---

## Skill Improvement

### Full Reference
👉 [adajoon-skill-improvement/SKILL.md](./adajoon-skill-improvement/SKILL.md)

### When to Use

Apply this skill during:
- Code reviews (note patterns violated)
- Bug postmortems (update skills to prevent recurrence)
- Security incidents (update immediately)
- Weekly reviews (aggregate learnings)
- Monthly audits (measure effectiveness)

### Process

**After Bugs**:
1. Document what happened
2. Root cause analysis
3. Fix implementation
4. Update relevant skill
5. Add prevention mechanism

**Weekly Review** (Fridays):
- Review skill violations
- Update unclear sections
- Document new patterns

**Monthly Audit** (1st of month):
- Analyze violation trends
- Measure bug prevention
- Identify skill gaps

### Learning Entry Template
```markdown
## Learning Entry #042

**Date**: 2026-04-04
**Category**: Database
**Mistake**: Missing transaction caused partial updates

## What Happened
User profile updated but preferences failed.

## Why
Transaction not wrapped in async context.

## The Fix
\`\`\`python
async with db.begin():
    await db.execute(update_user)
    await db.execute(update_preferences)
\`\`\`

## Skill Update
- **Skill**: adajoon-database
- **Section**: Transaction Patterns
- **Version**: v1.4.0
```

---

## Common Scenarios

### 🔧 "Review my authentication code"

```
@CLAUDE.md I need you to review my authentication implementation.
Check for:
- Cookie security (httpOnly, secure, samesite)
- JWT secret validation
- CSRF protection on mutations
- Rate limiting on login
```

**What to check**:
- [Security > Cookie Security](#security)
- [Security > JWT Validation](#security)
- [Backend > CSRF Protection](#backend-fastapi)
- [Security > Rate Limiting](#security)

---

### 🔧 "Create a new API endpoint"

```
@CLAUDE.md I need to create a new API endpoint for managing playlists.
Follow these patterns:
- Router structure
- Authentication
- CSRF protection
- Caching
- Database queries
```

**Reference sections**:
- [Backend > Router Structure](#backend-fastapi)
- [Backend > Authentication](#backend-fastapi)
- [Backend > CSRF Protection](#backend-fastapi)
- [Backend > Caching](#backend-fastapi)
- [Database > Query Patterns](#database)

---

### 🔧 "Create a new React component"

```
@CLAUDE.md I need to create a playlist management component.
Follow these patterns:
- Custom hooks (Context + Provider)
- API calls with authenticatedFetch
- Loading states
- Error handling
```

**Reference sections**:
- [Frontend > Custom Hooks Pattern](#frontend-react)
- [Frontend > API Client](#frontend-react)
- [Frontend > Loading States](#frontend-react)

---

### 🔧 "Create a database migration"

```
@CLAUDE.md I need to add a playlists table.
Follow these patterns:
- Migration template
- Proper timestamps
- Foreign keys with indexes
- IF NOT EXISTS syntax
```

**Reference sections**:
- [Database > Migration Template](#database)
- [Database > Model Patterns](#database)

---

### 🔧 "Fix a security issue"

```
@CLAUDE.md I found a security vulnerability in the user input handling.
Check against:
- Input validation patterns
- XSS prevention
- SQL injection prevention
- Update the security skill after fixing
```

**Reference sections**:
- [Security > Input Validation](#security)
- [Skill Improvement > After Bugs](#skill-improvement)

---

### 🔧 "Deploy a new service"

```
@CLAUDE.md I'm deploying a background worker service.
Ensure:
- All shared environment variables are set (JWT_SECRET, DATABASE_URL, etc.)
- Multi-stage Docker build
- Health checks
- Migrations run on startup
```

**Reference sections**:
- [Deployment > Environment Variables](#deployment)
- [Deployment > Docker Multi-Stage Build](#deployment)
- [Deployment > Deployment Checklist](#deployment)

---

## Skill Files Locations

For complete details, reference the full skill files:

1. **Backend**: `.cursor/skills/adajoon-backend/SKILL.md` (407 lines)
2. **Frontend**: `.cursor/skills/adajoon-frontend/SKILL.md` (~400 lines)
3. **Security**: `.cursor/skills/adajoon-security/SKILL.md` (531 lines)
4. **Database**: `.cursor/skills/adajoon-database/SKILL.md` (404 lines)
5. **Deployment**: `.cursor/skills/adajoon-deployment/SKILL.md` (~450 lines)
6. **Conventions**: `.cursor/skills/adajoon-conventions/SKILL.md` (435 lines)
7. **Skill Improvement**: `.cursor/skills/adajoon-skill-improvement/SKILL.md` (~940 lines)

**Total**: ~2,867 lines of comprehensive guidelines

---

## How to Use This File

### In Cursor (with @-mentions)

1. **Quick reference**: `@CLAUDE.md what are the CSRF rules?`
2. **Code review**: `@CLAUDE.md review this auth code against security patterns`
3. **New feature**: `@CLAUDE.md create a new playlist API endpoint following backend patterns`
4. **Debugging**: `@CLAUDE.md this migration failed, check against database patterns`

### In Direct Claude Conversations

Copy the relevant section from this file into your conversation:

```
I'm working on authentication in my Adajoon project. Here are the patterns I should follow:

[Paste Backend > Authentication section]

Please review my code against these patterns...
```

### Quick Pattern Lookup

Use your editor's search (Cmd/Ctrl+F) to find:
- `authenticatedFetch` → Frontend API patterns
- `verify_csrf_token` → CSRF protection
- `DateTime(timezone=True)` → Database timestamps
- `httponly=True` → Cookie security
- `Alembic` → Database migrations
- `multi-stage` → Docker builds

---

## Known Issues & Lessons Learned (2026-04-07)

### Incidents Resolved

1. **502 Bad Gateway** (v2.5.1): Frontend nginx was proxying to `backend:8000` but Railway runs services on port 8080 internally. Fixed in `start.sh` default BACKEND_URL.

2. **iOS Safari Black Screen** (v2.5.2): Three compounding causes:
   - `height: -webkit-fill-available` on `#root` computed to 0 on iOS Safari → all content clipped by `overflow: hidden`
   - Synchronous `<script>` tags (Chromecast SDK, IMA SDK) blocked iOS Safari's HTML parser
   - Nginx `try_files` caching gotcha: `Cache-Control` headers on `location = /index.html` don't apply when index.html is served via `try_files` from `location /` — Safari cached stale HTML

3. **Railway Agent keyboard interception**: Railway's AI Agent feature captures typed input in the dashboard. Workaround: use Railway CLI or GraphQL API instead of the UI for service management.

### Rules to Follow

- **CSS**: Never use `-webkit-fill-available` for height. Use `100vh` + `100dvh` fallback pattern.
- **Scripts**: Always load third-party SDKs with `async defer`. Never block the parser.
- **Nginx**: Always add no-cache headers to BOTH `location = /index.html` AND `location /` blocks.
- **Railway ports**: Private networking always uses port **8080**, regardless of what `EXPOSE` says in the Dockerfile.
- **Diagnostics**: Keep the inline `window.onerror` handler and loading fallback in `index.html` — they make future mobile debugging possible.
- **Testing**: After any CSS or HTML change, test on iOS Safari (private browsing to bypass cache).

## What Should Be Done Next

### High Priority
- [ ] **Update GitHub remote URL**: Remote still points to old `RevestTech/ReTV.git` — should be `RevestTech/Adajoon.git`
- [ ] **Re-enable Service Worker** with proper cache-first strategy for assets, network-first for HTML
- [ ] **Add error monitoring** (Sentry or similar) to catch mobile JS errors in production
- [ ] **Test on Android Chrome** and other mobile browsers for parity

### Medium Priority
- [ ] **Code-split more aggressively**: Main bundle is 727KB — consider splitting by route/feature
- [ ] **Add PWA offline support** once Service Worker is re-enabled
- [ ] **Remove `upgrade-insecure-requests` CSP meta tag** if not needed (can cause subtle issues on mobile)
- [ ] **Remove redundant `redirect.js`**: Server-side nginx redirect handles non-www → www, client-side JS redirect is no longer needed

### Low Priority
- [ ] **Update version in App.jsx footer**: Still shows v2.5.0, should be v2.5.2
- [ ] **Clean up TV debug overlay** for production (TVDebugInfo component)
- [ ] **Add automated Lighthouse CI** to catch mobile performance regressions

---

## Version

Created for Adajoon v2.3.0 (April 2026)
Last updated: 2026-04-07 (v2.5.2 — iOS Safari fix, nginx caching fix, deployment workflow)

Skills are continuously improved through the [Skill Improvement](#skill-improvement) process.
