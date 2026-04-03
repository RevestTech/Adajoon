# Production Incident Prevention Plan

## Executive Summary
**Incident:** Site loading timeout (April 3, 2026)  
**Cause:** Redis connection without timeout + no graceful degradation  
**Impact:** Complete site outage for ~30 minutes  
**Resolution Time:** 30 minutes

This document outlines measures to prevent similar incidents.

---

## 1. Pre-Deployment Checklist ✅

### Before Every Production Deploy:

#### A. Code Review Requirements
```
[ ] All new external dependencies have timeouts configured
[ ] All new database queries have reasonable limits
[ ] Error handling includes graceful degradation
[ ] New features have feature flags for easy rollback
[ ] No hardcoded secrets or API keys
```

#### B. Testing Requirements
```
[ ] Unit tests pass (backend + frontend)
[ ] Integration tests pass
[ ] Load test with 100+ concurrent users
[ ] Dependency failure test (Redis down, DB slow, etc.)
[ ] Health check endpoints still work
```

#### C. Monitoring Setup
```
[ ] New endpoints added to monitoring
[ ] Alerts configured for response time > 5s
[ ] Alerts configured for error rate > 1%
[ ] Logs include correlation IDs for tracing
```

---

## 2. Staging Environment 🎭

### Setup Required:
**Railway Projects:**
- Production: `adajoon-prod` (existing)
- Staging: `adajoon-staging` (NEW - needs creation)

### Staging Configuration:
```yaml
Environment: staging
Database: Separate PostgreSQL instance (Railway)
Redis: Separate Redis instance (Railway)
Domain: staging.adajoon.com
Data: Copy of production (anonymized)
```

### Staging Workflow:
1. Merge PR to `staging` branch
2. Auto-deploy to staging environment
3. Run automated tests
4. Manual QA testing
5. If all pass → merge to `main` → deploy to production

### Cost:
- ~$10/month (Railway staging environment)
- Worth it to prevent outages

---

## 3. Improved Health Checks 🏥

### Current Issue:
`/api/health` only checks if server is running, not if critical paths work.

### New Implementation:

**File:** `backend/app/routers/health.py`

```python
from fastapi import APIRouter, HTTPException
from datetime import datetime
import time

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health")
async def basic_health():
    """Quick health check - no dependencies"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Comprehensive readiness check.
    Tests all critical dependencies.
    """
    checks = {}
    start = time.time()
    
    # 1. Database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
    
    # 2. Redis
    try:
        redis_ok = await health_check()  # from redis_client
        checks["redis"] = "ok" if redis_ok else "degraded"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"
    
    # 3. Critical Query (categories - the one that failed)
    try:
        query_start = time.time()
        from app.services.channel_service import get_categories_with_counts
        rows = await get_categories_with_counts(db)
        query_time = (time.time() - query_start) * 1000
        checks["categories_query"] = f"ok ({len(rows)} rows in {query_time:.0f}ms)"
        
        if query_time > 5000:  # Warn if > 5 seconds
            checks["categories_query"] = f"slow ({query_time:.0f}ms)"
    except Exception as e:
        checks["categories_query"] = f"error: {str(e)}"
    
    total_time = (time.time() - start) * 1000
    
    # Determine overall status
    has_errors = any("error" in str(v) for v in checks.values())
    has_slow = "slow" in str(checks.get("categories_query", ""))
    
    status = "unhealthy" if has_errors else ("degraded" if has_slow else "healthy")
    
    return {
        "status": status,
        "checks": checks,
        "total_time_ms": round(total_time, 2),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes-style liveness check.
    Should never fail unless process is deadlocked.
    """
    return {"status": "alive"}
```

**Railway Health Check URL:** Change from `/api/health` to `/api/health/ready`

---

## 4. Monitoring & Alerting 📊

### A. Application Monitoring (Required)

**Option 1: Sentry (Recommended)**
```bash
# Free tier: 5K errors/month
pip install sentry-sdk[fastapi]
```

**Setup:**
```python
# backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if settings.env == "production":
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment="production",
        traces_sample_rate=0.1,  # 10% of requests
        profiles_sample_rate=0.1,
    )
```

**Alerts to Configure:**
- API response time > 5 seconds
- Error rate > 1%
- Redis connection failures
- Database query timeouts

**Option 2: Better Stack (formerly Logtail)**
- Free tier: 1GB logs/month
- Structured logging with search
- Alerting on patterns

### B. Uptime Monitoring (Required)

**BetterUptime (Free Tier)**
- Monitor: https://www.adajoon.com
- Monitor: https://backend-production-d32d8.up.railway.app/api/health/ready
- Check every: 1 minute
- Alert via: Email, Slack, SMS

**Alerts:**
- Site down (> 30s timeout)
- Health check fails
- Response time > 10s

**Cost:** Free for 1 site, 3 monitors

### C. Real User Monitoring (Optional)

**PostHog (Already Integrated)**
- Track page load times
- Monitor JS errors
- Track API call failures from frontend

---

## 5. Deployment Safety 🚀

### A. Deployment Process

**Current (Unsafe):**
```
git push → Railway auto-deploys → Hope it works
```

**New (Safe):**
```
1. Create PR
2. CI runs tests
3. Deploy to staging
4. Manual QA on staging
5. Merge to main
6. Deploy to production with health check
7. Monitor for 10 minutes
8. If issues: instant rollback
```

### B. Rollback Strategy

**Railway Rollback:**
```bash
# Via Railway CLI
railway rollback

# Or via web dashboard:
# Project → Deployments → Click previous deployment → Deploy
```

**Time to Rollback:** < 2 minutes

### C. Feature Flags

**For risky features, add toggle:**

```python
# backend/app/config.py
class Settings(BaseSettings):
    # Feature Flags
    enable_redis_cache: bool = os.getenv("ENABLE_REDIS_CACHE", "true").lower() == "true"
    enable_recommendations: bool = True
    enable_ads: bool = True
```

**Usage:**
```python
@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    # Try cache only if feature is enabled
    if settings.enable_redis_cache:
        cached = await cache_get("categories")
        if cached is not None:
            return cached
    
    # Always fall back to database
    rows = await get_categories_with_counts(db)
    # ...
```

**Disable feature without redeploying:**
```bash
# In Railway dashboard, add env var:
ENABLE_REDIS_CACHE=false

# Feature is instantly disabled, no deploy needed
```

---

## 6. Code Quality Standards 📐

### A. Dependency Rules

**All external dependencies MUST have:**
```python
# ❌ BAD: No timeout
redis_client = redis.from_url(url)

# ✅ GOOD: Timeout configured
redis_client = redis.from_url(
    url,
    socket_connect_timeout=2,
    socket_timeout=2,
)

# ❌ BAD: Raises on failure
def get_cache():
    client = await connect_redis()
    return await client.get(key)

# ✅ GOOD: Graceful degradation
def get_cache():
    try:
        client = await connect_redis()
        if client is None:
            return None
        return await client.get(key)
    except Exception as e:
        logger.warning(f"Cache error: {e}")
        return None
```

### B. Database Query Rules

**All queries MUST have:**
```python
# ❌ BAD: No limit
query = select(Channel)

# ✅ GOOD: Limited
query = select(Channel).limit(1000)

# ✅ GOOD: Timeout at connection level (done)
engine = create_async_engine(
    url,
    connect_args={
        "server_settings": {
            "statement_timeout": "10000",  # 10s
        }
    }
)
```

### C. API Endpoint Rules

**All endpoints MUST:**
```python
@router.get("/expensive-operation")
async def expensive_op():
    try:
        # 1. Check cache first
        cached = await cache_get("key")
        if cached:
            return cached
        
        # 2. Do expensive work with timeout
        result = await slow_operation()
        
        # 3. Cache result
        await cache_set("key", result, ttl=300)
        
        return result
    except Exception as e:
        # 4. Log error with context
        logger.error(f"Operation failed: {e}", exc_info=True)
        
        # 5. Return graceful error
        raise HTTPException(
            status_code=500,
            detail="Service temporarily unavailable"
        )
```

---

## 7. Testing Requirements 🧪

### A. Unit Tests (Required)

**Coverage Requirements:**
- Overall: > 70%
- Critical paths (auth, payments): > 90%
- New features: > 80%

### B. Integration Tests (Required)

**Test scenarios:**
```python
# Test: Redis down
async def test_categories_without_redis():
    # Disable Redis
    with mock.patch("app.redis_client.get_redis", return_value=None):
        response = await client.get("/api/categories")
        assert response.status_code == 200  # Should still work!

# Test: Slow database
async def test_categories_slow_db():
    # Simulate 15s query (should timeout at 10s)
    with mock.patch("app.services.channel_service.get_categories_with_counts") as mock_query:
        mock_query.side_effect = asyncio.TimeoutError()
        response = await client.get("/api/categories")
        assert response.status_code == 500
        assert "timeout" in response.json()["detail"].lower()

# Test: Cache poisoning
async def test_categories_invalid_cache():
    # Put invalid data in cache
    await cache_set("categories", "INVALID_JSON")
    response = await client.get("/api/categories")
    assert response.status_code == 200  # Should fall back to DB
```

### C. Load Tests (Before Major Releases)

**Tool:** Locust (Python) or k6 (Go)

**Test scenario:**
```python
# locustfile.py
from locust import HttpUser, task, between

class AdajoonUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(10)  # 10x weight - most common
    def browse_channels(self):
        self.client.get("/api/channels?limit=20")
    
    @task(5)
    def browse_categories(self):
        self.client.get("/api/categories")
    
    @task(3)
    def search(self):
        self.client.get("/api/channels?query=news")
    
    @task(1)
    def view_channel(self):
        self.client.get("/api/channels/1001Noites.br")

# Run test:
# locust -f locustfile.py --host https://backend-production-d32d8.up.railway.app
```

**Target metrics:**
- 100 concurrent users
- < 3s average response time
- < 1% error rate
- No timeouts

---

## 8. Incident Response Plan 🚨

### When Site Goes Down:

#### Step 1: Immediate Response (0-5 min)
```bash
1. Check Railway logs: railway logs --tail 100
2. Check health: curl https://backend.../api/health/ready
3. If Redis issue: Set ENABLE_REDIS_CACHE=false in Railway
4. If DB issue: Rollback deployment
5. Notify users via status page (if available)
```

#### Step 2: Investigation (5-15 min)
```bash
1. Check monitoring dashboard (Sentry/logs)
2. Identify root cause
3. Check recent deployments
4. Review recent changes to affected code
```

#### Step 3: Resolution (15-30 min)
```bash
1. Apply hotfix OR rollback
2. Test fix in staging (if time permits)
3. Deploy fix to production
4. Monitor for 10 minutes
5. Verify site is working
```

#### Step 4: Post-Mortem (Within 24 hours)
```markdown
1. What happened?
2. What was the impact?
3. What was the root cause?
4. How was it fixed?
5. How do we prevent it?
6. Action items with owners and deadlines
```

---

## 9. Immediate Action Items 🎯

### Priority 1 (This Week):
- [ ] Create staging environment on Railway
- [ ] Implement `/api/health/ready` endpoint
- [ ] Set up BetterUptime monitoring (free)
- [ ] Add pre-deployment checklist to README
- [ ] Document rollback process

### Priority 2 (Next 2 Weeks):
- [ ] Set up Sentry error tracking
- [ ] Add integration tests for dependency failures
- [ ] Create load testing script
- [ ] Add feature flags for risky features
- [ ] Document incident response process

### Priority 3 (Next Month):
- [ ] Achieve 70%+ test coverage
- [ ] Set up automated staging deployments
- [ ] Create runbook for common issues
- [ ] Add chaos testing (randomly kill Redis, etc.)
- [ ] Performance benchmarking suite

---

## 10. Cost Summary 💰

| Service | Purpose | Cost |
|---------|---------|------|
| Railway Staging | Testing environment | $10/month |
| BetterUptime | Uptime monitoring | Free |
| Sentry | Error tracking | Free (5K errors/month) |
| Better Stack | Log management | Free (1GB/month) |
| **Total** | | **~$10/month** |

**ROI:** One outage costs way more than $10/month in:
- Lost users
- Lost trust
- Developer time debugging
- Stress and reputation damage

---

## 11. Success Metrics 📈

### Track These:
- **MTBF** (Mean Time Between Failures): Target > 30 days
- **MTTR** (Mean Time To Recovery): Target < 15 minutes
- **Deployment Success Rate**: Target > 95%
- **Test Coverage**: Target > 70%
- **P95 Response Time**: Target < 2 seconds

### Monthly Review:
- Number of incidents
- Deployment frequency
- Test coverage trend
- Performance trends
- User feedback

---

## Conclusion

**The key lesson:** Always assume external dependencies will fail.

**The solution:** Defense in depth:
1. Timeouts on everything
2. Graceful degradation
3. Comprehensive health checks
4. Staging environment
5. Monitoring & alerting
6. Fast rollback capability
7. Feature flags for risk mitigation

**Investment:** ~$10/month + 2-3 days of initial setup  
**Benefit:** Prevented outages, faster incident response, better sleep

---

**Next Steps:** Review this plan with the team and assign owners to each Priority 1 item.
