# Manual Railway Domain Setup Required

## Current Status

✅ **All code fixes are complete and deployed:**
- Backend authentication (cookie-based JWT)
- COOP security headers (`unsafe-none`)
- Frontend proxy in backend
- CSP with OAuth domains
- Environment variables set

⚠️ **Remaining manual step:** Add custom domains to backend service in Railway Dashboard

## Why Manual Setup is Needed

The Railway CLI cannot add custom domains - this is a dashboard-only feature. Attempting to add them via CLI or API doesn't persist the changes.

## Instructions

### Step 1: Add Domains to Backend Service

1. Go to your project: https://railway.com/project/b34434ab-c40a-40bc-9d57-4b61d8c1a1a6

2. Click on **Backend** service

3. Go to **Settings** → **Domains**

4. Click **"+ Add Domain"**
   - Enter: `adajoon.com`
   - Click Save/Add

5. Click **"+ Add Domain"** again
   - Enter: `www.adajoon.com`
   - Click Save/Add

### Step 2: Verify Domains are Listed

You should now see in the Backend service's Domains section:
- `adajoon.com` ✅
- `www.adajoon.com` ✅
- (Plus the Railway-generated URLs)

### Step 3: Wait for Propagation

Railway needs to:
- Provision SSL certificates for the domains
- Update edge routing configuration
- Propagate changes globally

**Wait time:** 5-15 minutes (sometimes up to 30 minutes for DNS)

### Step 4: Test the Fix

After waiting, run these tests:

#### Test 1: Check COOP Headers
```bash
curl -sI "https://adajoon.com/" | grep -i "cross-origin"
```

**Expected output:**
```
cross-origin-opener-policy: unsafe-none
cross-origin-embedder-policy: unsafe-none
```

If you see these headers, the routing is working! ✅

**If you DON'T see them,** you'll see something like:
```
server: railway-edge
x-railway-cdn-edge: fastly/...
```
This means it's still routing through the frontend service.

#### Test 2: Check Full Headers
```bash
curl -sI "https://adajoon.com/"
```

Look for:
- ✅ **Backend routing:** Will show various security headers
- ❌ **Frontend routing:** Will show `x-railway-cdn-edge: fastly/...` without COOP headers

#### Test 3: Test OAuth Login

1. Open **incognito/private window** (critical for cache bypass)
2. Go to `https://adajoon.com`
3. Click "Sign in with Google"
4. Complete OAuth flow

**Expected result:**
- No COOP error in console ✅
- Login succeeds ✅
- User profile visible ✅

## How It Works

### Current Architecture

```
User Browser
    ↓ (requests adajoon.com)
    ↓
Railway Backend Service (with COOP headers)
    ↓ (proxies to)
    ↓
Railway Frontend Service (returns HTML/JS/CSS)
    ↓ (returns to)
    ↓
Railway Backend Service (adds security headers)
    ↓ (returns to)
    ↓
User Browser (receives response with COOP headers)
```

### Backend Proxy Logic

The backend has a catch-all route that:
1. Receives requests for non-API paths (like `/`, `/index.html`, `/assets/*`)
2. Proxies them to the frontend service
3. Returns the frontend's response
4. Backend's security middleware adds COOP headers

See `backend/app/main.py` lines 234-265 for the implementation.

### Why This Fixes OAuth

**Before:**
- `adajoon.com` → Frontend service
- Railway's CDN strips COOP headers
- Google OAuth sees missing/wrong COOP
- OAuth fails with "window.postMessage blocked"

**After:**
- `adajoon.com` → Backend service
- Backend adds COOP headers
- Google OAuth works correctly

## Troubleshooting

### If Headers Still Missing After 15 Minutes

1. **Clear browser cache:**
   - Hard refresh: Cmd+Shift+R (Mac) / Ctrl+Shift+R (Windows)
   - Or use incognito window

2. **Check domain configuration:**
   - Verify domains are on **backend** service
   - Verify domains are **NOT** on frontend service
   - Railway CLI: `railway service backend && railway domain`

3. **Check DNS:**
   ```bash
   dig adajoon.com +short
   ```
   Should resolve to Railway's IP (will be same as before, Railway handles routing internally)

4. **Check SSL certificate:**
   ```bash
   curl -v "https://adajoon.com/" 2>&1 | grep "subject:"
   ```
   Should show: `subject: CN=adajoon.com`

### If OAuth Still Fails After Headers Work

Check browser console for:
- 401 errors → Authentication issue (should be fixed)
- CORS errors → Check CORS_ORIGINS environment variable
- CSP errors → Check Content-Security-Policy header includes OAuth domains

## Summary

**Code:** ✅ All fixed and deployed
**Infrastructure:** ⏳ Needs manual domain configuration in Railway Dashboard
**Testing:** ⏳ Test after domain propagation (5-15 minutes)

Once domains are added to backend service, OAuth login will work immediately!

## Files Modified (For Reference)

- `backend/app/middleware/security_headers.py` - COOP headers
- `backend/app/routers/auth.py` - Cookie-based authentication
- `backend/app/main.py` - Frontend proxy
- `frontend/nginx.conf.template` - Frontend COOP headers (now bypassed)
- Multiple documentation files

## Support Links

- Railway Project: https://railway.com/project/b34434ab-c40a-40bc-9d57-4b61d8c1a1a6
- GitHub Repo: https://github.com/RevestTech/Adajoon.git
- Backend Service: https://backend-production-d32d8.up.railway.app
- Frontend Service: https://frontend-production-d863.up.railway.app
