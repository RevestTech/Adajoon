# Railway Domain Configuration Guide

## Current Issue
The middleware code is deployed, but `adajoon.com` (non-www) isn't reaching the backend. Railway needs both domains configured to route traffic properly.

## Railway Configuration Steps

### Step 1: Configure Backend Service Domains

1. **Open Railway Dashboard**
   - Go to https://railway.app
   - Navigate to your project
   - Select the **Backend** service

2. **Add Custom Domains**
   - Click **Settings** → **Domains**
   - You should see something like: `backend-production-XXXX.up.railway.app`
   
3. **Add BOTH Custom Domains:**
   ```
   www.adajoon.com (Primary)
   adajoon.com     (Will redirect to www)
   ```
   
4. **Update DNS Records** (if not already done)
   
   For **www.adajoon.com**:
   ```
   Type: CNAME
   Name: www
   Value: backend-production-XXXX.up.railway.app
   ```
   
   For **adajoon.com** (apex domain):
   ```
   Type: A
   Name: @
   Value: <Railway's IP> (Railway will provide this)
   ```
   OR
   ```
   Type: ALIAS/ANAME (Cloudflare/AWS Route53)
   Name: @
   Value: backend-production-XXXX.up.railway.app
   ```

### Step 2: Verify Environment Variables

Ensure these are set in Railway Backend service:

```bash
ENV=production
DATABASE_URL=<your-postgres-url>
REDIS_URL=<your-redis-url>
JWT_SECRET=<your-32+-char-secret>
GOOGLE_CLIENT_ID=<your-google-client-id>
APPLE_CLIENT_ID=<your-apple-client-id>
WEBAUTHN_RP_ID=adajoon.com
WEBAUTHN_ORIGIN=https://www.adajoon.com
CORS_ORIGINS=https://adajoon.com,https://www.adajoon.com
```

### Step 3: Verify Deployment

Wait 2-3 minutes after adding domains, then test:

```bash
# Test www (should work)
curl https://www.adajoon.com/api/health
# Expected: {"status":"ok"}

# Test non-www (should redirect)
curl -I https://adajoon.com/api/health
# Expected: HTTP/2 301 + Location: https://www.adajoon.com/api/health

# Test with redirect follow
curl -L https://adajoon.com/api/categories
# Expected: JSON array of categories
```

## Alternative: Railway Domain Redirect (If Above Doesn't Work)

If Railway doesn't support apex domain routing, use their redirect feature:

1. In Railway Dashboard → Backend Service → Settings → Domains
2. Add redirect rule:
   ```
   From: adajoon.com
   To: www.adajoon.com
   Type: Permanent (301)
   ```

## Frontend Service Configuration

The frontend should point to the backend. Verify:

1. Railway Dashboard → Frontend Service → Settings → Environment Variables
2. Set:
   ```
   BACKEND_URL=https://www.adajoon.com
   ```

## DNS Provider Configuration

### If using Cloudflare:
1. DNS → Add Record
   ```
   Type: CNAME
   Name: www
   Target: backend-production-XXXX.up.railway.app
   Proxy status: ✅ Proxied (Orange cloud)
   ```

2. For apex domain (`adajoon.com`):
   ```
   Type: CNAME
   Name: @
   Target: backend-production-XXXX.up.railway.app
   Proxy status: ✅ Proxied
   ```

### If using Other DNS Providers:
- Check if they support ALIAS/ANAME records for apex domains
- Otherwise, use A records pointing to Railway's IP

## Testing Checklist

After configuration, test these:

- [ ] `https://www.adajoon.com/api/health` returns `{"status":"ok"}`
- [ ] `https://www.adajoon.com/api/categories` returns JSON array
- [ ] `https://www.adajoon.com/api/csrf/token` returns CSRF token
- [ ] `https://adajoon.com/api/health` redirects to www (301)
- [ ] Service Worker no longer caches 404s
- [ ] Google OAuth login works end-to-end

## Troubleshooting

### Issue: "adajoon.com" still returns 404
**Cause**: Domain not added to Railway service  
**Fix**: Add `adajoon.com` in Railway Dashboard → Backend → Settings → Domains

### Issue: DNS not resolving
**Cause**: DNS propagation delay  
**Fix**: Wait 5-15 minutes, clear DNS cache: `sudo dscacheutil -flushcache` (macOS)

### Issue: Redirect not working
**Cause**: Wrong `ENV` variable (not "production")  
**Fix**: Set `ENV=production` in Railway environment variables

### Issue: SSL certificate errors
**Cause**: Railway hasn't provisioned SSL for new domain  
**Fix**: Wait 2-5 minutes after adding domain, Railway auto-provisions Let's Encrypt certs

## Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  User Browser                                                │
│  https://adajoon.com/                                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  Railway (Backend Service)                                   │
│  - Receives traffic for both domains                         │
│  - WWWRedirectMiddleware checks host header                 │
│  - If host == "adajoon.com" → 301 to www.adajoon.com       │
│  - If host == "www.adajoon.com" → Process request          │
└─────────────────────────────────────────────────────────────┘
```

## Quick Fix (Temporary)

While waiting for DNS/Railway config, you can manually clear Service Worker:

1. Open https://www.adajoon.com (use www directly)
2. F12 → Application → Service Workers → Unregister
3. Application → Storage → Clear site data
4. Hard refresh (Cmd+Shift+R)
5. Bookmark/use www.adajoon.com directly

This bypasses the non-www issue entirely until Railway is configured.
