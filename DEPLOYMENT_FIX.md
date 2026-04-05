# Deployment Fix: Non-WWW Domain Issues

## Problem Summary
- ✅ `www.adajoon.com` works correctly
- ❌ `adajoon.com` (non-www) returns 404 for all API endpoints
- ❌ Service Worker cached 404 responses
- ❌ Google OAuth login fails due to missing CSRF token

## Changes Made

### 1. Backend Changes
- **Added**: `backend/app/middleware/www_redirect.py` - Redirects non-www to www in production
- **Updated**: `backend/app/main.py` - Registered WWW redirect middleware

### 2. Frontend Changes
- **Updated**: `frontend/public/sw.js` - Bumped cache version to v2.4.0, prevents caching error responses
- **Updated**: `frontend/index.html` - Added auto-reload on Service Worker updates

## Railway Configuration Required

### Backend Service
1. Go to Railway Dashboard → Backend Service → Settings → Domains
2. Ensure BOTH domains are added:
   - `www.adajoon.com` (Primary)
   - `adajoon.com` (Will redirect to www)

### Frontend Service
1. Go to Railway Dashboard → Frontend Service → Settings → Domains
2. Ensure proper domain configuration
3. Verify `BACKEND_URL` environment variable points to backend service

### Environment Variables (Production)
Verify these are set in Railway:

**Backend Service:**
```
ENV=production
DATABASE_URL=<your-postgres-url>
REDIS_URL=<your-redis-url>
JWT_SECRET=<your-jwt-secret>
CORS_ORIGINS=https://adajoon.com,https://www.adajoon.com
GOOGLE_CLIENT_ID=<your-google-client-id>
APPLE_CLIENT_ID=<your-apple-client-id>
WEBAUTHN_RP_ID=adajoon.com
WEBAUTHN_ORIGIN=https://www.adajoon.com
```

**Frontend Service:**
```
BACKEND_URL=<your-backend-railway-url>
```

## Deployment Steps

1. **Commit Changes:**
   ```bash
   git add backend/app/middleware/www_redirect.py backend/app/main.py
   git add frontend/public/sw.js frontend/index.html
   git commit -m "fix: redirect non-www to www, fix service worker caching"
   git push origin main
   ```

2. **Wait for Railway Auto-Deploy** (5-10 minutes)

3. **Verify Backend:**
   ```bash
   # Should return 301 redirect
   curl -I https://adajoon.com/api/health
   
   # Should return 200 OK
   curl -I https://www.adajoon.com/api/health
   ```

4. **Clear Service Worker Cache:**
   - Open `https://adajoon.com` in browser
   - Open DevTools (F12) → Application → Service Workers
   - Click "Unregister"
   - Application → Storage → Clear site data
   - Hard refresh (Cmd+Shift+R / Ctrl+Shift+F5)
   - Reload page - new SW should install automatically

5. **Test OAuth Login:**
   - Click "Sign in with Google"
   - Complete OAuth flow
   - Should redirect to homepage logged in

## Testing Checklist

- [ ] Backend health check works: `https://www.adajoon.com/api/health`
- [ ] Categories endpoint works: `https://www.adajoon.com/api/categories`
- [ ] CSRF token endpoint works: `https://www.adajoon.com/api/csrf/token`
- [ ] Non-www redirects to www: `https://adajoon.com` → `https://www.adajoon.com`
- [ ] Service Worker registers without errors
- [ ] Google OAuth login completes successfully
- [ ] User redirected to homepage after login

## Troubleshooting

### Issue: Still getting 404s
**Solution**: Verify both domains are added in Railway backend service settings

### Issue: Service Worker still serving old cache
**Solution**: 
1. Unregister SW in DevTools
2. Clear all site data
3. Hard refresh (Cmd+Shift+R)
4. Wait 60 seconds for auto-reload with new SW

### Issue: OAuth popup blocked
**Solution**: Ensure COOP header is `unsafe-none` (already configured in SecurityHeadersMiddleware)

### Issue: Cookies not working across domains
**Solution**: Verify `cookie_domain = ".adajoon.com"` is set in production (already configured)

## Architecture Notes

```
User → https://adajoon.com
     ↓ (301 Redirect via WWWRedirectMiddleware)
     → https://www.adajoon.com (Railway Backend)
     → API responses with cookies (domain: .adajoon.com)
     → OAuth works (COOP: unsafe-none)
```

## Files Changed
- `backend/app/middleware/www_redirect.py` (new)
- `backend/app/main.py` (modified)
- `frontend/public/sw.js` (modified)
- `frontend/index.html` (modified)
