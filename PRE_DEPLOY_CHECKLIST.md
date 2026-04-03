# Pre-Deployment Checklist

Use this checklist before deploying to production to prevent outages.

## Code Quality ✅

- [ ] All tests pass locally
  ```bash
  cd backend && pytest
  cd frontend && npm test
  ```

- [ ] No linting errors
  ```bash
  cd backend && ruff check .
  cd frontend && npm run lint
  ```

- [ ] Code reviewed by at least one person

## Dependency Safety ✅

- [ ] All new external dependencies have timeouts
  - Redis: `socket_connect_timeout`, `socket_timeout`
  - HTTP clients: `timeout` parameter
  - Database: `statement_timeout`, `command_timeout`

- [ ] All new database queries have limits
  - `.limit(1000)` on potentially large queries
  - Pagination on list endpoints

- [ ] Graceful degradation implemented for optional services
  - Redis down → fall back to database
  - External API down → return cached data or error
  - Slow query → timeout and return partial results

## Configuration ✅

- [ ] No hardcoded secrets in code
- [ ] All required environment variables documented in `.env.example`
- [ ] Feature flags configured for risky features
- [ ] CORS origins include production domain

## Health & Monitoring ✅

- [ ] Health check endpoint still works: `/api/health/ready`
  ```bash
  curl https://backend-production-d32d8.up.railway.app/api/health/ready
  # Should return {"status":"healthy",...} in < 10 seconds
  ```

- [ ] New endpoints return proper error codes (not 500 for user errors)
- [ ] Logging includes context (user_id, request_id, etc.)

## Testing ✅

- [ ] Test with Redis disabled
  ```bash
  export ENABLE_REDIS_CACHE=false
  # Run app and verify it still works
  ```

- [ ] Test with slow database (optional, advanced)
  ```python
  # Add artificial delay in query
  await asyncio.sleep(11)  # Should timeout at 10s
  ```

- [ ] Load test with production data size (if significant changes)
  ```bash
  # Use Locust or k6 to simulate 100 concurrent users
  ```

## Rollback Plan ✅

- [ ] Know how to rollback in Railway
  - Dashboard → Project → Deployments → Previous deployment → Deploy
  - Or CLI: `railway rollback`

- [ ] Communicate deployment to team
  - Slack/email: "Deploying v2.3.0 at 2pm PT, watching for 15 mins"

- [ ] Monitor after deployment for 10-15 minutes
  - Check logs for errors
  - Check `/api/health/ready`
  - Test critical user flows (login, browse, play)

## Post-Deployment ✅

- [ ] Verify site loads: https://www.adajoon.com
- [ ] Check backend health: https://backend-production-d32d8.up.railway.app/api/health/ready
- [ ] Monitor error rates in Sentry (when set up)
- [ ] Check response times in logs

## If Something Breaks 🚨

**Immediate actions:**
1. Check Railway logs: `railway logs --tail 100`
2. Check health endpoint: `curl .../api/health/ready`
3. If critical, rollback immediately
4. If minor, disable feature via env var (if using feature flags)
5. Notify team

**Do NOT:**
- Push fixes without testing
- Panic-deploy multiple times
- Hide the issue

---

## Quick Reference

### Check Health
```bash
curl https://backend-production-d32d8.up.railway.app/api/health/ready
```

### View Logs
```bash
railway logs --tail 100
# Or in Railway dashboard → Deployments → View logs
```

### Rollback
```bash
railway rollback
# Or in dashboard → Deployments → Click previous → Deploy
```

### Disable Feature
```bash
# In Railway dashboard → Variables → Add:
ENABLE_REDIS_CACHE=false
```

---

**Remember:** It's better to delay a deployment than to cause an outage.
**Time saved by skipping checks: 5 minutes**
**Time lost from outage: 30+ minutes + user trust**
