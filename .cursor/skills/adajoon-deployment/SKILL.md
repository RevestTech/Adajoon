# Adajoon Deployment & Railway Patterns

**Version**: 1.2.0 (Updated: 2026-04-07)

**Skill Type:** Deployment, Infrastructure, Docker
**Auto-triggers:** When working with Dockerfiles, Railway configuration, deployment scripts, nginx configs, or environment variables

## Changelog
- v1.2.0 (2026-04-07): Added iOS Safari compatibility rules, nginx caching gotcha (`try_files` location context), and mobile debugging patterns after black screen incident
- v1.1.0 (2026-04-07): Added Railway port mapping gotcha, private networking patterns, service naming, and Railway API/CLI usage notes after 502 incident
- v1.0.1 (2026-04-04): Added environment variable parity checklist after worker JWT_SECRET incident
- v1.0.0 (2026-04-04): Initial versioning - established baseline deployment patterns

---

## Overview

This skill enforces Adajoon's Railway deployment architecture and best practices. The system uses a **dual-service pattern** where all traffic flows through the backend service, which proxies to the frontend for security headers and centralized control.

---

## Railway Architecture

### Service Structure

```
Railway Deployment:
├── backend (Python FastAPI)
│   ├── Public domain: adajoon.com
│   ├── Handles: /api/* routes
│   ├── Proxies: / and /assets/* to frontend service
│   └── Adds: Security headers via middleware
└── frontend (React + Nginx)
    ├── Internal service URL only
    ├── Not publicly exposed
    └── Accessed only via backend proxy
```

### Why This Architecture?

1. **Security Headers:** Backend middleware applies security headers to all responses
2. **Single Public Domain:** Simplifies SSL/DNS management
3. **Centralized Logging:** All requests flow through backend for monitoring
4. **CORS Control:** Backend manages CORS policies
5. **API Rate Limiting:** Backend applies rate limits before reaching frontend

---

## Docker Multi-Stage Builds

### Backend Pattern (Python)

```dockerfile
# Stage 1: Builder - Compile dependencies
FROM python:3.12-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Stage 2: Runtime - Minimal image
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt && rm -rf /wheels
COPY . .
RUN chmod +x start.sh
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health').read()" || exit 1
CMD ["./start.sh"]
```

**Key Points:**
- Separate builder stage with build tools (gcc, libpq-dev)
- Runtime stage only has runtime deps (libpq5)
- Use `pip wheel` to pre-compile packages
- Remove /wheels after install to reduce image size
- Health check uses Python built-in urllib
- Always clean apt cache with `rm -rf /var/lib/apt/lists/*`

### Frontend Pattern (React + Nginx)

```dockerfile
# Stage 1: Build - Compile React app
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve - Nginx static serving
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/conf.d/default.conf.template
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY start.sh /start.sh
RUN chmod +x /start.sh
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1
CMD ["/start.sh"]
```

**Key Points:**
- Use alpine images for smaller size
- Build stage uses full node:20-alpine
- Runtime stage uses nginx:alpine (tiny)
- Copy only /dist output, not source files
- Health check uses wget (available in nginx:alpine)
- nginx.conf.template for Railway env var substitution

---

## ⚠️ Railway Port Mapping (CRITICAL)

Railway assigns its own port to services via the `PORT` environment variable (typically **8080**). This overrides whatever port the Dockerfile `EXPOSE` or `start.sh` defaults to.

### The Gotcha

The backend Dockerfile says `EXPOSE 8000` and `start.sh` defaults to `--port ${PORT:-8000}`, but Railway sets `PORT=8080`. When services communicate via **private networking** (`.railway.internal`), you must use the Railway-assigned port, not the Dockerfile default.

```
❌ WRONG: http://backend.railway.internal:8000   (Dockerfile default)
❌ WRONG: http://backend:8000                     (no .railway.internal suffix)
✅ RIGHT: http://backend.railway.internal:8080    (Railway-assigned port)
```

### Frontend start.sh Pattern

```sh
#!/bin/sh
export PORT=${PORT:-80}
export BACKEND_URL=${BACKEND_URL:-http://backend.railway.internal:8080}
envsubst '${PORT} ${BACKEND_URL}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf
nginx -g 'daemon off;'
```

### How to Debug 502 Errors

1. Check Railway deploy logs for `connect() failed (111: Connection refused)`
2. Note which port is being refused — if it's 8000, you have a port mismatch
3. Verify the `BACKEND_URL` env var on the frontend service in Railway dashboard
4. If not set, check `frontend/start.sh` default value
5. The correct internal URL is always: `http://<service-name>.railway.internal:8080`

### Railway Private Networking Rules

- Use `<service-name>.railway.internal` for service-to-service communication
- The service name in the URL must match the Railway service name exactly
- Port is always whatever Railway assigns via `PORT` env var (usually 8080)
- Private networking only works within the same Railway project and environment

---

## Railway Service Management

### Naming Conventions

| Service | Railway Name | Purpose |
|---------|-------------|---------|
| Frontend | `frontend` | React SPA served by nginx |
| Backend | `backend` | FastAPI API server |
| Worker | `worker` | Background task processor |
| Redis | `Redis` | Cache and session store |
| Postgres | `Postgres` | Primary database |

### Railway CLI Commands (Authenticated as khash@khash.com)

```bash
# Status and info
railway status                    # Show linked project/service/environment
railway whoami                    # Verify authentication
railway deployment list           # List recent deployments with status

# Deploying
railway service frontend          # Switch to frontend service context
railway up --detach               # Upload local dir and deploy (non-blocking)
railway deployment redeploy       # Redeploy the latest deployment

# Debugging
railway service logs              # View service logs (live tail)
railway variables                 # List env vars for current service
```

**Deploy workflow** (preferred):
1. Make code changes, commit to `main`
2. `git push origin main` (triggers auto-deploy if configured)
3. If auto-deploy doesn't trigger: `cd frontend && railway service frontend && railway up --detach`
4. `railway deployment list` to verify SUCCESS

### Railway GraphQL API (for automation)

The Railway CLI stores an access token at `~/.config/railway/config.json` under `user.accessToken`. This can be used with the GraphQL API:

```bash
curl -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"query":"mutation { serviceUpdate(id: \"<SERVICE_ID>\", input: { name: \"new-name\" }) { id name } }"}'
```

Useful operations: rename services, update env vars, delete orphaned services, list all services in a project.

**⚠️ Warning**: Do NOT use Railway's dashboard UI for typing-heavy operations (renaming, etc.) — Railway's Agent feature intercepts keyboard input. Use the CLI or GraphQL API instead.

---

## Environment Variable Configuration

### Backend Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host/db

# Redis
REDIS_URL=redis://host:6379/0

# Frontend proxy (Railway service URL)
FRONTEND_URL=https://frontend-production-d863.up.railway.app

# Logging
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
JSON_LOGS=true              # Structured JSON logs for production

# Security
SYNC_API_KEY=your-secret-key-here  # For /api/sync endpoint
CORS_ORIGINS=["https://adajoon.com"]

# Features
ENABLE_INITIAL_SYNC=1       # Run data sync on startup
ENABLE_METRICS=1            # Enable Prometheus metrics

# OAuth (if applicable)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

### Frontend Environment Variables

```bash
# Backend proxy (Railway service URL)
BACKEND_URL=https://backend-production-xyz.up.railway.app

# Nginx port (Railway provides PORT automatically)
PORT=80
```

### Local vs Railway

**Local Development:**
```bash
# Backend
DATABASE_URL=postgresql+asyncpg://localhost/adajoon
REDIS_URL=redis://localhost:6379/0
FRONTEND_URL=http://localhost:5173
JSON_LOGS=false

# Frontend
BACKEND_URL=http://localhost:8000
PORT=80
```

**Railway Production:**
```bash
# Backend
DATABASE_URL=${{Postgres.DATABASE_URL}}  # Railway reference
REDIS_URL=${{Redis.REDIS_URL}}
FRONTEND_URL=${{frontend.RAILWAY_PUBLIC_DOMAIN}}
JSON_LOGS=true

# Frontend
BACKEND_URL=${{backend.RAILWAY_PRIVATE_DOMAIN}}
PORT=${{PORT}}  # Railway provides this
```

### ⚠️ Environment Variable Parity Checklist

**CRITICAL:** When deploying multiple services that share code (backend, worker, etc.), ensure ALL services have required shared environment variables.

#### Required for All Python Services

```bash
# Security (REQUIRED - validated at startup)
✅ JWT_SECRET          # 32+ chars, shared across all services
✅ DATABASE_URL        # Same Postgres instance  
✅ REDIS_URL           # Same Redis instance
✅ ENVIRONMENT         # prod/staging/dev
```

#### Railway Reference Pattern

Use Railway's reference variables to share secrets:

```bash
# In worker service:
JWT_SECRET = ${{backend.JWT_SECRET}}
DATABASE_URL = ${{Postgres.DATABASE_URL}}
REDIS_URL = ${{Redis.REDIS_URL}}
```

#### Pre-Deployment Checklist

1. Copy shared env vars from existing service
2. Verify: `railway variables | grep JWT_SECRET`
3. Test startup logs for "Database initialization complete"

**Incident:** [2026-04-04 worker crash](../adajoon-skill-improvement/learnings/2026-04-04-worker-jwt-secret-missing.md) - Missing JWT_SECRET

---

## Frontend Proxy Pattern

### Backend Proxy Implementation

```python
# In backend/app/main.py
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://frontend-production-d863.up.railway.app")
http_client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

async def _proxy_to_frontend(request: Request, path: str = ""):
    """Helper to proxy requests to frontend."""
    url = f"{FRONTEND_URL}/{path}"
    if request.url.query:
        url = f"{url}?{request.url.query}"
    
    try:
        response = await http_client.get(
            url,
            headers={k: v for k, v in request.headers.items() 
                    if k.lower() not in ['host', 'connection']},
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers={
                k: v for k, v in response.headers.items() 
                if k.lower() not in ['content-encoding', 'content-length', 
                                    'transfer-encoding', 'connection']
            },
        )
    except Exception as e:
        logger.error(f"Frontend proxy error: {e}")
        raise HTTPException(status_code=502, detail="Frontend service unavailable")

# Routes
@app.get("/")
async def serve_root(request: Request):
    return await _proxy_to_frontend(request, "")

@app.get("/assets/{path:path}")
async def serve_assets(request: Request, path: str):
    return await _proxy_to_frontend(request, f"assets/{path}")

@app.get("/{page:path}")
async def serve_page(request: Request, page: str):
    # Block API routes from frontend proxy
    if page == "api" or page.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    return await _proxy_to_frontend(request, page)
```

**Critical Rules:**
1. Use `httpx.AsyncClient` with connection pooling (create once, reuse)
2. Forward query strings with `request.url.query`
3. Filter headers: exclude `host`, `connection` in request
4. Filter headers: exclude encoding/length headers in response
5. Return proper error (502) if frontend unavailable
6. **Explicitly block `/api` routes** from frontend proxy

### Nginx Configuration Template

```nginx
# frontend/nginx.conf.template
server {
    listen ${PORT};
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Redirect non-www to www (only in production)
    if ($host = 'adajoon.com') {
        return 301 https://www.adajoon.com$request_uri;
    }

    # Security headers
    add_header Cross-Origin-Embedder-Policy "unsafe-none" always;

    # Proxy /api/* to backend
    location /api/ {
        proxy_pass ${BACKEND_URL}/api/;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        proxy_buffering on;
        proxy_buffer_size 8k;
        proxy_buffers 8 16k;
    }

    # Cache static assets (hashed filenames — safe to cache forever)
    location /assets/ {
        add_header Cache-Control "public, max-age=31536000, immutable";
        try_files $uri =404;
    }

    # No cache for index.html (direct access)
    location = /index.html {
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0" always;
        add_header Pragma "no-cache" always;
        add_header Expires "0" always;
        add_header Cross-Origin-Embedder-Policy "unsafe-none" always;
    }

    # SPA fallback — MUST also have no-cache headers
    # ⚠️ CRITICAL: try_files serves index.html from THIS location context,
    # NOT from `location = /index.html`. Without no-cache here, browsers
    # (especially iOS Safari) will cache stale HTML indefinitely.
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0" always;
        add_header Pragma "no-cache" always;
        add_header Cross-Origin-Embedder-Policy "unsafe-none" always;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 256;
    gzip_comp_level 5;
    gzip_types text/plain text/css application/json application/javascript
               text/xml application/xml application/xml+rss text/javascript
               image/svg+xml;
}
```

### ⚠️ Nginx `try_files` Caching Gotcha (CRITICAL)

When using `try_files $uri $uri/ /index.html` for SPA routing, `Cache-Control` headers
set in `location = /index.html` do **NOT** apply. Nginx serves the file from the
**matching location block** (`location /`), not the named file's location. This caused
a major iOS Safari caching bug where users saw a stale black-screen HTML for days.

**Rule**: Always add no-cache headers to the `location /` block when using `try_files`.

### iOS Safari / Mobile Compatibility Rules

1. **Never use `height: -webkit-fill-available`** — can compute to 0 on iOS Safari, causing invisible content with `overflow: hidden`. Use `100vh` + `100dvh` instead.
2. **Always load external SDKs with `async defer`** — synchronous scripts block the iOS Safari HTML parser. If the script stalls (CDN slow, not supported), the entire page is blank.
3. **Always provide `vh` fallbacks before `dvh`** — `dvh` is only supported on iOS 15.4+.
4. **Include inline fallback content** in `<div id="root">` — visible text that shows while React loads, so failures aren't invisible black screens.
5. **Include inline `window.onerror`** — catches and displays JS errors visually for mobile debugging (no dev tools available).

**Template Substitution Script (start.sh):**
```bash
#!/bin/sh
envsubst '${PORT} ${BACKEND_URL}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf
nginx -g 'daemon off;'
```

---

## Health Check Endpoints

### Backend Health Checks

```python
@app.get("/api/health")
async def health():
    """Simple liveness check."""
    return {"status": "ok"}

@app.get("/api/health/ready")
async def health_ready(db: AsyncSession = Depends(get_db)):
    """Comprehensive readiness check."""
    checks = {}
    overall_status = "healthy"
    
    # Database check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok"}
    except Exception as e:
        checks["database"] = {"status": "error", "message": str(e)}
        overall_status = "unhealthy"
    
    # Redis check (optional)
    try:
        redis_ok = await redis_health_check()
        checks["redis"] = {"status": "ok" if redis_ok else "degraded"}
    except Exception as e:
        checks["redis"] = {"status": "degraded", "message": str(e)}
    
    return {"status": overall_status, "checks": checks}
```

**Health Check Strategy:**
- `/api/health`: Fast liveness check (no DB queries)
- `/api/health/ready`: Readiness check (tests DB, Redis)
- Dockerfile uses liveness check only
- Railway can use both for monitoring

---

## Logging Configuration

### Structured JSON Logs for Production

```python
# backend/app/logging_config.py pattern
import logging
import sys
import json
from datetime import datetime

def setup_logging(log_level: str = "INFO", json_logs: bool = True):
    """Configure structured logging."""
    
    if json_logs:
        # Production: JSON structured logs
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                }
                if record.exc_info:
                    log_data["exception"] = self.formatException(record.exc_info)
                return json.dumps(log_data)
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
    else:
        # Development: Human-readable logs
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
    
    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper()))
    root.handlers.clear()
    root.addHandler(handler)
```

**Usage:**
```python
# In main.py
log_level = os.getenv("LOG_LEVEL", "INFO")
json_logs = os.getenv("JSON_LOGS", "true").lower() in ("true", "1", "yes")
setup_logging(log_level=log_level, json_logs=json_logs)
```

---

## Database Migrations

### Alembic on Deployment

```bash
# backend/start.sh
#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Migration Workflow:**
1. **Development:** Create migration with `alembic revision --autogenerate -m "description"`
2. **Review:** Check generated migration in `alembic/versions/`
3. **Test:** Run `alembic upgrade head` locally
4. **Deploy:** Railway runs `start.sh` which applies migrations automatically
5. **Rollback:** Use `alembic downgrade -1` if needed

**Critical Rules:**
- Never skip migrations in production
- Always run migrations before starting app
- Test migrations on staging first
- Use `alembic upgrade head` not `Base.metadata.create_all()`
- Migrations run automatically on Railway deploy

---

## Manual Data Sync

### SYNC_API_KEY Endpoint

```python
SYNC_API_KEY = os.getenv("SYNC_API_KEY", "")

@app.post("/api/sync")
async def trigger_sync(x_sync_key: str | None = Header(default=None, alias="X-Sync-Key")):
    """Manually trigger a data sync (requires SYNC_API_KEY header)."""
    if not SYNC_API_KEY:
        raise HTTPException(
            status_code=503, 
            detail="Sync endpoint is disabled (SYNC_API_KEY not configured)"
        )
    
    # Constant-time comparison to prevent timing attacks
    import secrets
    if not x_sync_key or not secrets.compare_digest(x_sync_key, SYNC_API_KEY):
        raise HTTPException(
            status_code=403, 
            detail="Invalid or missing X-Sync-Key header"
        )
    
    async with async_session() as db:
        results = await full_sync(db)
    return {"status": "complete", "results": results}
```

**Usage:**
```bash
curl -X POST https://adajoon.com/api/sync \
  -H "X-Sync-Key: your-secret-key"
```

**Security:**
- Use `secrets.compare_digest()` to prevent timing attacks
- Return generic error message (don't reveal if key is wrong)
- Only enable if `SYNC_API_KEY` is configured
- Use strong random key (generate with `openssl rand -hex 32`)

---

## Build Optimization

### Backend: Poetry to Requirements.txt

```bash
# In CI/CD or before deploy
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

**Why?**
- Poetry is slow in Docker builds
- requirements.txt with pip is faster
- Export without hashes for better Docker layer caching

### Frontend: npm ci vs npm install

```dockerfile
# ❌ BAD: Slower, modifies package-lock.json
RUN npm install

# ✅ GOOD: Faster, uses exact versions from lock file
RUN npm ci --only=production
```

**Why?**
- `npm ci` is faster (uses lockfile directly)
- Doesn't modify package-lock.json
- Fails if package.json and lock are out of sync (catches errors)

---

## Deployment Checklist

### Before Deploying

- [ ] Database migrations tested locally (`alembic upgrade head`)
- [ ] Environment variables configured in Railway
- [ ] `FRONTEND_URL` points to frontend service
- [ ] `BACKEND_URL` points to backend service
- [ ] `JSON_LOGS=true` for production
- [ ] `SYNC_API_KEY` set to strong random value
- [ ] Health checks return 200 OK
- [ ] CORS origins include production domain

### Railway Service Configuration

**Backend Service:**
- Root Directory: `backend/`
- Build Command: (uses Dockerfile)
- Start Command: (uses Dockerfile CMD)
- Port: 8000
- Public Domain: adajoon.com
- Health Check Path: `/api/health`

**Frontend Service:**
- Root Directory: `frontend/`
- Build Command: (uses Dockerfile)
- Start Command: (uses Dockerfile CMD)
- Port: 80
- Public Domain: NONE (internal only)
- Health Check Path: `/`

---

## Common Pitfalls

### 1. Frontend Publicly Exposed
❌ **Wrong:** Frontend has its own public domain  
✅ **Right:** Frontend only accessible via backend proxy

### 2. Missing Health Checks
❌ **Wrong:** No health check in Dockerfile  
✅ **Right:** Both services have HEALTHCHECK instruction

### 3. Large Docker Images
❌ **Wrong:** Single-stage build with all dependencies  
✅ **Right:** Multi-stage build, remove build tools in final image

### 4. Hardcoded URLs
❌ **Wrong:** `FRONTEND_URL = "https://frontend.railway.app"`  
✅ **Right:** `FRONTEND_URL = os.getenv("FRONTEND_URL")`

### 5. Migrations Not Running
❌ **Wrong:** Only `uvicorn app.main:app` in start.sh  
✅ **Right:** `alembic upgrade head` before starting server

### 6. Insecure Sync Endpoint
❌ **Wrong:** No authentication on `/api/sync`  
✅ **Right:** `X-Sync-Key` header with `secrets.compare_digest()`

---

## Quick Reference

### Railway Service URLs

```bash
# Backend internal URL (for frontend to call API)
${{backend.RAILWAY_PRIVATE_DOMAIN}}

# Frontend internal URL (for backend to proxy)
${{frontend.RAILWAY_PRIVATE_DOMAIN}}

# Public backend URL
${{backend.RAILWAY_PUBLIC_DOMAIN}}
```

### Port Conventions

- Backend: 8000 (FastAPI default)
- Frontend: 80 (Nginx default)
- Railway: Uses $PORT env var (bind to 0.0.0.0:$PORT)

### Docker Build Commands

```bash
# Backend
docker build -t adajoon-backend -f backend/Dockerfile backend/

# Frontend
docker build -t adajoon-frontend -f frontend/Dockerfile frontend/
```

---

## When to Trigger This Skill

Use this skill when:
- Creating or modifying Dockerfiles
- Configuring Railway services
- Setting up environment variables
- Implementing proxy patterns
- Adding health check endpoints
- Configuring logging
- Setting up database migrations
- Implementing secure endpoints (like sync)
- Optimizing build times
- Debugging deployment issues

---

## Enforcement Rules

1. **Never** expose frontend service publicly on Railway
2. **Always** use multi-stage Docker builds
3. **Always** include health checks in Dockerfile
4. **Always** run migrations in start.sh before app starts
5. **Always** use structured JSON logs in production (JSON_LOGS=true)
6. **Always** use environment variables for service URLs
7. **Always** use secrets.compare_digest() for API key validation
8. **Always** proxy through backend for security headers
9. **Always** use nginx.conf.template with envsubst for frontend
10. **Always** clean apt cache in Dockerfiles to reduce image size

---

## Related Files

- `backend/Dockerfile` - Backend multi-stage build
- `frontend/Dockerfile` - Frontend multi-stage build
- `frontend/nginx.conf.template` - Nginx config with env vars
- `backend/app/main.py` - Backend proxy implementation
- `backend/start.sh` - Deployment startup script
- `backend/alembic/` - Database migrations
- `backend/app/logging_config.py` - Structured logging setup
