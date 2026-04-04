# Learning: Worker Service Missing JWT_SECRET

**Date**: 2026-04-04  
**Severity**: High (Service Down)  
**Affected Service**: worker  
**Time to Resolution**: ~5 minutes  

## What Happened

The worker container crashed on startup with the following error:

```python
File "/app/app/config.py", line 97, in validate_config
    raise ValueError(error_msg)
ValueError: JWT_SECRET validation failed
```

**Root Cause**: The `JWT_SECRET` environment variable was not set on the worker service in Railway, causing the config validation to fail at startup.

## Why It Happened

1. **Missing Environment Variable**: When deploying the worker service, `JWT_SECRET` was not added to its environment variables
2. **Config Validation**: The `settings.validate_config()` enforces JWT_SECRET at startup (as per security skill v1.0.0)
3. **Service Isolation**: Each Railway service has its own environment variables - setting it on backend doesn't automatically set it on worker

## The Fix

Added `JWT_SECRET` environment variable to the worker service:

```bash
# In Railway Dashboard or CLI:
JWT_SECRET=2e5224dd44413cd1c8b7930b8e83a840f1357c95bbe9b...
```

Worker service redeployed and now starting successfully:
```
2026-04-04 20:31:58,634 [INFO] app.worker: Validator worker starting
```

## Prevention Strategy

### Immediate Actions
1. ✅ JWT_SECRET added to worker service
2. ✅ Verified worker is running
3. ⏳ Check all other services have required env vars

### Skill Updates Required

**Update: `adajoon-deployment` skill**

Add section on **Environment Variable Parity Across Services**:

```markdown
## Environment Variable Checklist

When deploying multiple services that share code (backend, worker, etc.), ensure ALL services have:

### Required for All Services
- ✅ `JWT_SECRET` - Authentication (32+ chars, validated at startup)
- ✅ `DATABASE_URL` - Database connection
- ✅ `REDIS_URL` - Cache and rate limiting
- ✅ `ENVIRONMENT` - prod/staging/dev

### Backend-Specific
- `STRIPE_WEBHOOK_SECRET` - Payment webhooks
- `CORS_ORIGINS` - Frontend domains
- `FRONTEND_URL` - For proxy pattern

### Worker-Specific
- `SYNC_API_KEY` - For triggering syncs
- `ENABLE_INITIAL_SYNC` - Whether to sync on startup

**Pro Tip**: Use Railway's "Reference Variables" to share secrets:
```bash
JWT_SECRET = ${{backend.JWT_SECRET}}
```
```

### Process Improvements

1. **Deployment Checklist**: Before deploying new service, verify all shared env vars are set
2. **Config Validation**: Already working well - caught the issue at startup ✅
3. **Monitoring**: Set up Railway alerts for service crashes
4. **Documentation**: Update deployment docs with env var checklist

## Affected Skills

- ✅ **adajoon-security** v1.0.0 - JWT_SECRET validation worked as expected
- 🔄 **adajoon-deployment** v1.0.0 → v1.0.1 - ADD env var parity section

## Metrics

- **Detection Time**: Immediate (startup validation)
- **Diagnosis Time**: ~2 minutes (error logs were clear)
- **Fix Time**: ~3 minutes (add env var + redeploy)
- **Total Downtime**: ~5 minutes
- **Recurrence Risk**: Low (after skill update)

## Related Skills

- [adajoon-deployment](../adajoon-deployment/SKILL.md) - Railway environment variables
- [adajoon-security](../adajoon-security/SKILL.md) - JWT_SECRET validation

## Action Items

- [x] Fix applied (JWT_SECRET added to worker)
- [x] Learning documented
- [ ] Update adajoon-deployment skill v1.0.0 → v1.0.1
- [ ] Verify all services have required env vars
- [ ] Add to weekly review on Friday

## Notes

This incident validates the importance of:
1. **Startup validation** - Fail fast with clear error messages
2. **Config centralization** - `settings.validate_config()` catches missing vars immediately
3. **Service isolation** - Each Railway service needs its own env var configuration
4. **Clear error messages** - ValueError made root cause obvious

**Lesson**: When adding new services that share code with existing services, copy ALL environment variables, not just service-specific ones.
