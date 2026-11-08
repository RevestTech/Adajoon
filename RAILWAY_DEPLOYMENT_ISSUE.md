# Railway Deployment Issue - April 6, 2026

## Problem
Production site at www.adajoon.com is serving OLD code with JavaScript initialization error despite multiple successful deployments.

## Root Cause Fixed
✅ **Fixed in commit `427daf8`**:
- Added missing `JWT_SECRET` and `REDIS_URL` to docker-compose.yml
- Fixed ReferenceError by moving `useTVNavigation` hook after variable declarations
- Code fix is correct and working locally

## Current Situation

### Local Environment
- ✅ **WORKING**: http://localhost:3000 serves fixed code (`index-YWzjxZEr.js`)
- ✅ All services healthy (backend, frontend, worker, db, redis)
- ✅ Fix verified and functional

### Production (Railway)
- ❌ **BROKEN**: www.adajoon.com still serving old code (`index-BjqqyJNZ.js`)
- ✅ Deployments showing "SUCCESS" status
- ❌ But Railway is serving cached/old build despite new commits

## What Was Attempted
1. `railway up --service frontend` - Build succeeded but served old code
2. `railway redeploy` - Redeployed but didn't rebuild from git
3. Empty commit push (6f85030) - Triggered webhook but still cached
4. Package.json modification (20389cd, 5af6bfc) - Build succeeded but served old assets  
5. Version bump to 2.5.1 (2346655) - Latest attempt, still serving old code
6. **2026-04-06 07:53**: Added cache-busting ARG to Dockerfile (3abefab) - Still serving old code
7. **2026-04-06 07:56**: Modified source file with build timestamp (ee21c46) - Still serving old code
8. **Waited 3+ minutes after each push** - Railway not rebuilding despite git webhooks

## Manual Action Required

### ⚠️ CRITICAL: Railway Git Integration Not Working

Railway is **NOT** detecting git pushes or rebuilding despite:
- ✅ Multiple successful git pushes to main branch
- ✅ Dockerfile cache-busting ARG added
- ✅ Source code modifications forcing new hashes
- ❌ Railway still serving cached Docker image from days ago

**This requires immediate manual intervention via Railway Dashboard.**

---

### Option 1: Railway Web Dashboard (RECOMMENDED)
1. Go to: https://railway.app/project/b34434ab-c40a-40bc-9d57-4b61d8c1a1a6/service/4beb6364-1e3d-4d96-a07c-52543055e3fe
2. Navigate to the **production** environment
3. Find the **frontend** service
4. Click **Settings** → **Delete all volumes/Clear cache** (if available)
5. Click **Deploy** → **Redeploy from Git** → Select commit `427daf8` or later
6. Watch build logs to ensure it's building fresh (not using cache)

### Option 2: Dockerfile Cache Bust
Add to `frontend/Dockerfile` before `COPY . .`:
```dockerfile
# Force cache bust
ARG CACHEBUST=1
```

Then redeploy with build args.

### Option 3: Contact Railway Support
The issue appears to be Railway caching the Docker image layers despite code changes. This might require:
- Clearing build cache on Railway's side
- Checking if Railway's git integration is properly syncing

## Verification
Once deployed correctly, check:
```bash
curl -sS https://www.adajoon.com/ | grep 'index-'
```

Should show: `src="/assets/index-YWzjxZEr.js"` (or newer)
NOT: `src="/assets/index-BjqqyJNZ.js"` (old broken version)

## Key Commits
- `427daf8` - **MAIN FIX**: Resolves JS initialization error ✅
- `5af6bfc` - Fixes invalid package.json comment
- `2346655` - Version bump to 2.5.1
- `3abefab` - Adds Dockerfile cache-busting ARG
- `ee21c46` - Forces new asset hashes via source modification (latest)
- ~~`6f85030`, `20389cd`~~ - Temporary rebuild triggers (can be squashed)

## Next Steps
1. **IMMEDIATE**: Manually trigger clean rebuild on Railway dashboard (see Option 1 above)
2. Verify production serves new assets (should see `index-*.js` with different hash)
3. Consider squashing the temporary rebuild commits
4. **INVESTIGATE**: Why Railway git webhooks stopped working
5. Update Railway deployment config to prevent future cache issues

## Troubleshooting Railway Git Integration

If Railway dashboard rebuild doesn't work:

1. **Check Railway Webhook Status**
   - Go to Project Settings → Integrations
   - Verify GitHub webhook is active
   - Check webhook delivery logs for failures

2. **Verify Railway GitHub App Permissions**
   - Ensure Railway GitHub App has repository access
   - Check if repository was renamed (repo shows as moved to RevestTech/Adajoon)

3. **Manual Redeploy via API** (if you have Railway API token)
   ```bash
   curl -X POST https://backboard.railway.app/graphql \
     -H "Authorization: Bearer $RAILWAY_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "mutation { serviceInstanceRedeploy(serviceId: \"4beb6364-1e3d-4d96-a07c-52543055e3fe\") }"
     }'
   ```

4. **Contact Railway Support**
   - Email: team@railway.app
   - Discord: https://discord.gg/railway
   - Mention: Stuck cache, git webhooks not triggering rebuilds
