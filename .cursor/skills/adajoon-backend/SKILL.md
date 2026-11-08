---
name: adajoon-backend
description: Enforces Adajoon backend FastAPI patterns including router structure, cookie-based JWT authentication, CSRF protection, Redis caching, structured logging, and database session management. Use when creating or editing backend routers, API endpoints, authentication code, or any FastAPI-related code in the backend/ directory.
---

# Adajoon Backend FastAPI Patterns

**Version**: 1.0.0 (Updated: 2026-04-04)

This skill enforces consistent patterns for Adajoon's FastAPI backend architecture.

## Changelog
- v1.0.0 (2026-04-04): Initial versioning - established baseline backend patterns

## Router Structure

All routers follow this pattern:

```python
import logging
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.redis_client import cache_get, cache_set

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/feature-name", tags=["feature-name"])

CACHE_TTL = 300  # 5 minutes
```

**Key rules:**
- **Prefix**: Always use `/api/` prefix for all API routes
- **Tags**: Set tags to match feature name for API docs grouping
- **Logger**: Use module-level logger with `logging.getLogger(__name__)`
- **Cache TTL**: Define constants at module level

## Authentication Patterns

### Cookie-Based JWT Authentication

Use cookie-based authentication (not Authorization headers) for new endpoints:

```python
from app.routers.auth import get_current_user, require_user
from app.models import User

# Optional authentication (returns None if not authenticated)
@router.get("/endpoint")
async def optional_auth_endpoint(
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if user:
        # User-specific logic
        pass
    # Public logic
    pass

# Required authentication (raises 401 if not authenticated)
@router.post("/protected")
async def protected_endpoint(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db)
):
    # user is guaranteed to be authenticated
    pass
```

### Setting Authentication Cookies

```python
from app.config import settings

def _set_auth_cookies(response: Response, user: User, token: str) -> None:
    cookie_domain = ".adajoon.com" if settings.env == "production" else None
    
    response.set_cookie(
        key="auth_token", value=token, httponly=True, secure=True,
        samesite="lax", max_age=settings.jwt_expiry_days * 24 * 60 * 60,
        path="/", domain=cookie_domain
    )
    
    response.set_cookie(
        key="csrf_token", value=csrf_token, httponly=False,
        secure=True, samesite="lax", max_age=3600,
        path="/", domain=cookie_domain
    )
```

**Rules:** Never return JWT in body; use httpOnly cookies. CSRF cookie must be readable. Use `.adajoon.com` domain in production.

## CSRF Protection

### Apply to Mutating Endpoints

Add CSRF validation to all POST/PUT/PATCH/DELETE endpoints that modify data:

```python
from app.csrf import verify_csrf_token

@router.post("/favorites")
async def add_favorite(
    body: FavoriteRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token)  # CSRF validation
):
    # Implementation
    pass

@router.delete("/favorites/{item_id}")
async def remove_favorite(
    item_id: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token)
):
    # Implementation
    pass
```

**CSRF rules:**
- **Apply** to all mutating operations (POST/PUT/PATCH/DELETE)
- **Skip** for read-only endpoints (GET)
- **Place** as the last dependency parameter with name `_csrf`
- **Combine** with `require_user` for authenticated mutations

## Request Logging

```python
logger = logging.getLogger(__name__)

@router.get("/endpoint")
async def endpoint(db: AsyncSession = Depends(get_db)):
    try:
        logger.info("Processing endpoint request")
        result = await operation(db)
        logger.info(f"Processed {len(result)} items")
        return result
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

**Rules:** Use `logger.info()` for operations, `logger.error()` with `exc_info=True` for exceptions. Include context (counts, IDs).

## Error Handling

```python
from fastapi import HTTPException, status

@router.get("/endpoint")
async def endpoint(db: AsyncSession = Depends(get_db)):
    try:
        if not valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input")
        
        result = await operation(db)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
```

**Rules:** Use `status.HTTP_*` constants. Re-raise HTTPExceptions. Log unexpected exceptions. Convert to 500 errors.

## Caching Patterns

```python
from app.redis_client import cache_get, cache_set, cache_delete

CACHE_TTL = 300  # 5 minutes

@router.get("/data", response_model=list[DataOut])
async def get_data(db: AsyncSession = Depends(get_db)):
    cached = await cache_get("data")
    if cached:
        return cached
    
    rows = await fetch_from_db(db)
    data = [DataOut.model_validate(row) for row in rows]
    await cache_set("data", [d.model_dump() for d in data], CACHE_TTL)
    return data

@router.post("/data")
async def create_data(
    body: DataCreate,
    user = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token)
):
    item = await create_item(db, body)
    await cache_delete("data")  # Invalidate cache
    return item
```

**Rules:** Cache read-heavy endpoints. Use descriptive keys. TTL: 300s dynamic, 3600s static. Serialize with `.model_dump()`. Invalidate on mutations.

## Database Session Management

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db

@router.get("/items")
async def list_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()

@router.post("/items")
async def create_item(
    body: ItemCreate,
    user = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token)
):
    item = Item(**body.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item
```

**Rules:** Use `get_db` dependency. Always async/await. Commit after mutations. Refresh to get updated fields. Use SQLAlchemy 2.0 syntax.

## Response Models and Validation

```python
from pydantic import BaseModel, Field

class ItemCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: str = ""

class ItemOut(BaseModel):
    id: int
    name: str
    description: str
    model_config = {"from_attributes": True}

@router.post("/items", response_model=ItemOut)
async def create_item(body: ItemCreate, user = Depends(require_user), db: AsyncSession = Depends(get_db)):
    item = Item(**body.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item
```

**Rules:** Define request/response models. Use Field validators. Set `model_config = {"from_attributes": True}` for ORM models.

## Rate Limiting

Apply rate limiting to sensitive endpoints:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

@router.post("/auth/login")
@limiter.limit("10/minute")
async def login(
    request: Request,  # Required for limiter
    body: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    # Implementation
    pass
```

**Rate limiting rules:**
- **Apply** to authentication endpoints (10/minute)
- **Apply** to expensive operations (custom limits)
- **Include** `Request` parameter when using `@limiter.limit`
- **Configure** in app setup (see main.py)

## Complete Router Example

Combine all patterns:

```python
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.database import get_db
from app.routers.auth import require_user
from app.csrf import verify_csrf_token
from app.redis_client import cache_get, cache_set, cache_delete
from app.models import Item

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/items", tags=["items"])
CACHE_TTL = 300

class ItemCreate(BaseModel):
    name: str = Field(..., max_length=255)

class ItemOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}

@router.get("/", response_model=list[ItemOut])
async def list_items(db: AsyncSession = Depends(get_db)):
    cached = await cache_get("items")
    if cached:
        return cached
    
    result = await db.execute(select(Item))
    data = [ItemOut.model_validate(i) for i in result.scalars().all()]
    await cache_set("items", [d.model_dump() for d in data], CACHE_TTL)
    return data

@router.post("/", response_model=ItemOut)
async def create_item(
    body: ItemCreate,
    user = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token)
):
    item = Item(**body.model_dump(), user_id=user.id)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    await cache_delete("items")
    return item
```

## Middleware and App Configuration

When modifying main.py, maintain this middleware order:

```python
# 1. Request logging (first to capture all requests)
app.add_middleware(RequestLoggingMiddleware)

# 2. GZip compression
app.add_middleware(GZipMiddleware, minimum_size=500)

# 3. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 4. CORS (last to add headers to all responses)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Lifespan Management

Use lifespan context manager for startup/shutdown:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")
    
    # Background tasks
    sync_task = asyncio.create_task(initial_sync())
    
    yield
    
    # Shutdown
    sync_task.cancel()
    await engine.dispose()
    logger.info("Cleanup complete")

app = FastAPI(lifespan=lifespan)
```

## Summary Checklist

When creating or modifying backend code:

- [ ] Router uses `/api/` prefix and appropriate tags
- [ ] Module-level logger defined with `logging.getLogger(__name__)`
- [ ] Authentication uses `get_current_user` or `require_user` dependencies
- [ ] Mutating endpoints include `verify_csrf_token` dependency
- [ ] Caching applied to read-heavy endpoints with appropriate TTL
- [ ] Cache invalidation on mutations
- [ ] Database operations use `get_db` dependency
- [ ] All queries use async/await syntax
- [ ] Request models have Field validators
- [ ] Response models specified with `response_model`
- [ ] Error handling with try/except and appropriate logging
- [ ] Rate limiting on sensitive endpoints
- [ ] Structured logging with context (counts, IDs, operations)
- [ ] Cookie-based authentication (not header-based) for new endpoints
- [ ] HTTPException uses status constants, not magic numbers
