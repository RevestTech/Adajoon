---
name: adajoon-conventions
description: Enforces Adajoon code quality standards and conventions across Python backend (FastAPI) and JavaScript/React frontend. Use when creating, editing, or reviewing any code in the Adajoon project to ensure consistency with naming conventions, import organization, type hints, async patterns, and comment guidelines.
---

# Adajoon Code Quality & Conventions

**Version**: 1.0.0 (Updated: 2026-04-04)

Enforces consistent code patterns across the Adajoon codebase.

## Changelog
- v1.0.0 (2026-04-04): Initial versioning - established baseline conventions

## Python Backend Standards

### Type Hints
**Required** for all function signatures, including return types:

```python
async def search_channels(db: AsyncSession, params: ChannelSearchParams) -> tuple[list[Channel], int]:
    channels, total = await get_data(db)
    return channels, total

def create_token(user_id: int, email: str) -> str:
    return jwt.encode(payload, settings.jwt_secret)
```

Use modern union syntax `str | None` (not `Optional[str]`):

```python
async def get_user(
    auth_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    pass
```

### Async/Await
All database operations and I/O must use async/await:

```python
result = await db.execute(select(User).where(User.id == user_id))
user = result.scalar_one_or_none()
```

### String Formatting
Use f-strings exclusively:

```python
logger.error(f"Failed to sync: {error}")
url = f"{BASE_URL}/api/{endpoint}?page={page}"
```

### List Comprehensions
Prefer list comprehensions over map/filter:

```python
ids = [i.strip() for i in item_ids.split(",") if i.strip()]
channels = [ChannelOut.model_validate(c) for c in results]
```

### Import Organization
Three sections with blank lines between:

```python
# Standard library
import asyncio
import logging
from datetime import datetime, timezone

# Third-party packages
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from pydantic import BaseModel

# Local imports
from app.database import get_db
from app.models import User, Channel
from app.config import settings
```

### Naming Conventions
- **Functions/Variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

```python
class UserFavorite(Base):
    pass

async def get_current_user(db: AsyncSession) -> User | None:
    pass

VALID_VOTE_TYPES = {"like", "dislike"}
_HIDDEN_CATEGORIES = {"xxx"}
```

### Pydantic Models
Use `model_config` for ORM compatibility:

```python
class ChannelOut(BaseModel):
    id: str
    name: str
    is_active: bool = True
    
    model_config = {"from_attributes": True}
```

### Error Handling
Use specific exception types with status codes:

```python
if not user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

if not channel:
    raise HTTPException(status_code=404, detail="Channel not found")
```

### Logging
Use structured logging with logger.method():

```python
logger = logging.getLogger(__name__)

logger.info("Database initialization complete")
logger.error("IPTV sync failed: %s", e)
logger.warning("Rate limit exceeded for %s", user_id)
```

### Comments
**AVOID** obvious/redundant comments. Only explain non-obvious intent:

```python
# ✅ GOOD - explains non-obvious constraint
SYNC_API_KEY = os.getenv("SYNC_API_KEY", "")  # Empty by default to disable endpoint

# ✅ GOOD - explains complex logic
# Constant-time comparison to prevent timing attacks
if not secrets.compare_digest(x_sync_key, SYNC_API_KEY):
    raise HTTPException(status_code=403)

# ❌ BAD - obvious from code
# Get the user from the database
user = await get_user(db, user_id)

# ❌ BAD - redundant
# Return the channels
return channels
```

### Configuration
Use settings object, not `os.getenv()` everywhere:

```python
# config.py - centralized configuration
class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "postgresql://...")
    jwt_secret: str = os.getenv("JWT_SECRET", "")

settings = Settings()

# Other files - use settings object
from app.config import settings

token = jwt.encode(payload, settings.jwt_secret)
```

### File Organization

```
backend/
├── app/
│   ├── routers/          # API endpoints (prefix=/api/...)
│   ├── services/         # Business logic
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas
│   ├── database.py       # DB connection
│   ├── config.py         # Settings
│   └── main.py           # App initialization
├── alembic/              # Database migrations
└── tests/                # Test files (test_*.py)
```

### API Routing
All backend routes use `/api` prefix:

```python
router = APIRouter(prefix="/api/channels", tags=["channels"])

@router.get("")  # Results in /api/channels
async def list_channels():
    pass

@router.get("/{channel_id}")  # Results in /api/channels/{channel_id}
async def get_channel(channel_id: str):
    pass
```

### Docstrings
Only for complex/non-obvious functions. Skip trivial ones:

```python
# ✅ GOOD - complex logic needs explanation
async def get_categories_with_counts(db: AsyncSession):
    """
    Returns categories with channel counts across multiple health statuses.
    Matches TV filter chips: 'live' = playable stream, 'verified' = fully verified.
    """
    pass

# ✅ GOOD - simple function, no docstring needed
async def get_channel_by_id(db: AsyncSession, channel_id: str):
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    return result.scalar_one_or_none()
```

---

## JavaScript/React Frontend Standards

### Variable Declarations
Use `const` by default, `let` when reassignment needed. **Never use `var`**:

```javascript
const user = await fetchUser();
let count = 0;
count++;
```

### Function Style
Use arrow functions consistently:

```javascript
const handleClick = () => {
  console.log("clicked");
};

const fetchData = async () => {
  const res = await fetch(url);
  return res.json();
};
```

### Async/Await
Use async/await for promises (not .then()):

```javascript
// ✅ GOOD
const data = await authenticatedFetch(`${API_BASE}/favorites`);
const json = await data.json();

// ❌ AVOID
fetch(url).then(res => res.json()).then(data => ...);
```

### Naming Conventions
- **Variables/Functions**: `camelCase`
- **Components**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Hooks**: `use` prefix

```javascript
const userName = "John";
const API_BASE = "/api";

function ChannelGrid({ channels, onSelect }) {
  const [loading, setLoading] = useState(false);
  return <div>...</div>;
}

function useAuth() {
  const [user, setUser] = useState(null);
  return { user };
}
```

### Component Files
Use `.jsx` extension for components:

```
components/
├── Header.jsx
├── ChannelGrid.jsx
├── VideoPlayer.jsx
└── LoginModal.jsx

hooks/
├── useAuth.jsx
├── useFavorites.js
└── useVotes.js
```

### Import Organization
React/libraries first, then local imports:

```javascript
import { useState, useEffect, useCallback } from "react";
import { startAuthentication } from "@simplewebauthn/browser";

import { authenticatedFetch } from "../utils/csrf";
import { useAuth } from "../hooks/useAuth";
```

### API Organization
Centralize API calls in `api/` directory:

```javascript
// api/channels.js
const BASE = "/api";

export async function fetchChannels({ query, category, page = 1 }) {
  const params = new URLSearchParams();
  if (query) params.set("query", query);
  params.set("page", page);
  
  const res = await fetch(`${BASE}/channels?${params}`);
  if (!res.ok) throw new Error("Failed to fetch channels");
  return res.json();
}
```

### Comments
Same as Python - only for non-obvious logic:

```javascript
// ✅ GOOD - explains complex state
// Determine cookie domain - use .adajoon.com for both www and non-www
const cookie_domain = ".adajoon.com";

// ✅ GOOD - clarifies non-obvious behavior
// Frontend needs to read this cookie (not httpOnly)
response.set_cookie(key="csrf_token", httponly=False)

// ❌ BAD - obvious
// Set the user state
setUser(data);

// ❌ BAD - redundant
// Fetch channels from API
const channels = await fetchChannels();
```

### Event Handlers
Prefix with `handle` or `on`:

```javascript
const handleChange = (e) => {
  setLocalSearch(e.target.value);
};

const onToggleFavorites = () => {
  setShowFavorites(!showFavorites);
};

<input onChange={handleChange} />
<button onClick={onToggleFavorites}>Toggle</button>
```

---

## Git Commit Messages

Use **Conventional Commits** format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, no logic change)
- `refactor`: Code restructuring (no feature/fix)
- `perf`: Performance improvement
- `test`: Add/update tests
- `chore`: Maintenance (deps, config)

### Examples

```
feat(auth): add passkey registration flow

Implement WebAuthn passkey registration with challenge tokens
and credential storage in PostgreSQL.

feat(channels): add health status filtering

fix(api): correct pagination calculation for favorites

refactor(frontend): extract channel card components

docs: update API documentation for /api/channels

chore(deps): upgrade fastapi to 0.109.0
```

### Scope Guidelines
- Backend: `auth`, `api`, `db`, `channels`, `radio`
- Frontend: `ui`, `components`, `hooks`, `api`
- Both: `config`, `deps`, `docker`

---

## Quality Checklist

Before committing code, verify:

### Python
- [ ] All functions have type hints (params + return)
- [ ] Using async/await for DB operations
- [ ] Using f-strings for formatting
- [ ] Imports organized (stdlib, third-party, local)
- [ ] snake_case naming
- [ ] Settings object (not os.getenv)
- [ ] Specific exception types
- [ ] No obvious/redundant comments
- [ ] Routes use `/api` prefix

### JavaScript/React
- [ ] Using const/let (no var)
- [ ] Arrow functions
- [ ] Async/await (not .then)
- [ ] camelCase naming, PascalCase components
- [ ] .jsx for component files
- [ ] Organized imports (React first, then local)
- [ ] No obvious/redundant comments

### General
- [ ] Conventional Commits format
- [ ] Consistent with existing patterns
- [ ] No generated comments explaining changes
