# Comprehensive Test Plan for Domain Fix

## What Was Fixed

### Issue 1: Non-WWW API Calls Returning 404
**Root Cause**: Frontend nginx wasn't redirecting `adajoon.com/api/*` to `www.adajoon.com/api/*`
**Fix**: Added nginx redirect rule that redirects ALL non-www traffic (including API paths) to www

### Issue 2: Service Worker Caching 404 Responses
**Root Cause**: Old Service Worker (v2.2.0) cached 404 responses before fix was deployed
**Fix**: Temporarily disabled Service Worker and added auto-cleanup script to unregister old SW and clear all caches

### Issue 3: OAuth Login Failing
**Root Cause**: CSRF token endpoint returning 404 due to Issue #1
**Fix**: Once domain redirect works, CSRF endpoint will be accessible and OAuth will work

## Files Changed

1. **frontend/nginx.conf.template**
   - Added: `if ($host = 'adajoon.com') { return 301 https://www.adajoon.com$request_uri; }`
   - Redirects ALL paths from non-www to www (including `/api/*`)

2. **frontend/public/redirect.js**
   - Client-side failsafe redirect that runs before React loads
   - Catches any requests that somehow bypass nginx redirect

3. **frontend/index.html**
   - Loads redirect.js immediately in `<body>` tag
   - Disabled Service Worker registration
   - Added cleanup script to unregister old SW and clear caches

## Expected Behavior After Deploy

### Scenario 1: User Visits `https://adajoon.com`
```
1. Browser requests: https://adajoon.com/
2. Nginx redirects: 301 → https://www.adajoon.com/
3. Browser loads: https://www.adajoon.com/
4. redirect.js checks hostname: www.adajoon.com ✅ (no action needed)
5. Old SW is unregistered, caches cleared
6. React app loads
7. All API calls use /api/* (relative URLs) → https://www.adajoon.com/api/*
```

### Scenario 2: User Visits `https://adajoon.com/api/categories`
```
1. Browser requests: https://adajoon.com/api/categories
2. Nginx redirects: 301 → https://www.adajoon.com/api/categories
3. Nginx proxies: → Backend /api/categories
4. Returns: JSON response with categories
```

### Scenario 3: User Clicks "Sign in with Google"
```
1. User on: https://www.adajoon.com
2. Frontend requests: /api/csrf/token (relative URL)
3. Nginx proxies: → Backend /api/csrf/token
4. Returns: {"csrf_token": "..."}
5. Google OAuth popup opens
6. User signs in
7. OAuth callback with token
8. Frontend calls: /api/auth/google (with CSRF token)
9. Backend validates and creates session
10. Frontend receives auth cookie
11. Redirect to homepage ✅
```

## Manual Testing Steps (After Deploy)

### Step 1: Verify Nginx Redirect
```bash
# Test redirect (should return 301)
curl -I https://adajoon.com/

# Expected:
# HTTP/2 301
# location: https://www.adajoon.com/

# Test API redirect (should return 301)
curl -I https://adajoon.com/api/health

# Expected:
# HTTP/2 301
# location: https://www.adajoon.com/api/health
```

### Step 2: Verify API Endpoints Work
```bash
# Test health endpoint
curl https://www.adajoon.com/api/health
# Expected: {"status":"ok"}

# Test categories endpoint
curl https://www.adajoon.com/api/categories | jq '.[0]'
# Expected: JSON object with category data

# Test CSRF token endpoint
curl https://www.adajoon.com/api/csrf/token
# Expected: {"csrf_token":"..."}
```

### Step 3: Verify Service Worker Cleanup
1. Open DevTools (F12) → Console
2. Look for these messages:
   ```
   [SW] Unregistered: https://adajoon.com/
   [Cache] Deleted: adajoon-v2.2.0
   [Cache] Deleted: adajoon-runtime
   ```
3. Go to Application tab → Service Workers
4. Should show: "No service workers registered"
5. Go to Application tab → Cache Storage
6. Should be empty or only contain new caches

### Step 4: Test Full OAuth Flow
1. Visit https://adajoon.com (should redirect to www)
2. Verify no console errors
3. Click "Sign in with Google"
4. Complete Google OAuth in popup
5. Popup should close
6. Should redirect to homepage
7. User should be logged in (check for user menu/avatar)

### Step 5: Verify No Console Errors
Open https://www.adajoon.com and check console for:
- ❌ No 404 errors for /api/* endpoints
- ❌ No "Failed to get CSRF token" errors
- ❌ No Service Worker caching errors
- ✅ May see: [SW] Unregistered / [Cache] Deleted (this is good!)
- ✅ Clean console after page loads

## Automated Testing Script

Run this after deployment:

```bash
#!/bin/bash
echo "=== Testing Non-WWW to WWW Redirect ==="
curl -I https://adajoon.com/ 2>&1 | grep -E "(HTTP|location)"
curl -I https://adajoon.com/api/health 2>&1 | grep -E "(HTTP|location)"

echo -e "\n=== Testing API Endpoints ==="
curl -s https://www.adajoon.com/api/health
echo ""
curl -s https://www.adajoon.com/api/categories | jq '.[0] // "Error"'
curl -s https://www.adajoon.com/api/csrf/token | jq '.csrf_token // "Error"'

echo -e "\n=== Testing Redirect Follow ==="
curl -L -s https://adajoon.com/api/health
echo ""

echo -e "\n=== All tests complete ==="
```

## Success Criteria

- [ ] `https://adajoon.com/` redirects to `https://www.adajoon.com/` (301)
- [ ] `https://adajoon.com/api/*` redirects to `https://www.adajoon.com/api/*` (301)
- [ ] All API endpoints return 200 OK (not 404)
- [ ] CSRF token endpoint works: `/api/csrf/token`
- [ ] Categories endpoint works: `/api/categories`
- [ ] Service Worker is unregistered
- [ ] Old caches are deleted
- [ ] No console errors on page load
- [ ] Google OAuth login completes successfully
- [ ] User is redirected to homepage after login
- [ ] User session persists (auth cookie set)

## Rollback Plan (If Needed)

If the deployment breaks something:

```bash
# Revert the commit
git revert HEAD
git push origin main

# Railway will auto-deploy the revert
```

## Timeline

- **Commit**: `a884bc4` - "fix: comprehensive solution for non-www domain issues"
- **Deploy**: ~5-10 minutes after push
- **Testing**: 5 minutes
- **Expected Resolution**: 15 minutes from now

## Known Limitations

1. **Service Worker Disabled**: Users won't have offline functionality until we re-enable it
2. **No PWA Install**: Install prompt won't appear while SW is disabled
3. **No Push Notifications**: Requires Service Worker

We can re-enable these features once the domain routing is stable for 24 hours.

## Post-Deploy Monitoring

Check Railway logs for:
- Nginx reload success
- No 404 errors in access logs
- Successful OAuth callback requests
- Session cookie creation
