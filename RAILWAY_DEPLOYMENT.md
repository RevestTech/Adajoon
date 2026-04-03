# Railway Deployment Guide

## Prerequisites
- Railway CLI installed (`brew install railway`)
- Railway account (sign up at railway.app)

## Quick Deploy Steps

### 1. Login to Railway
```bash
railway login
```

### 2. Initialize Project
```bash
cd /Users/khashsarrafi/Projects/Adajoon
railway init
```

### 3. Add PostgreSQL Database
```bash
railway add --plugin postgresql
```

### 4. Set Environment Variables

Get the database URL from Railway:
```bash
railway variables
```

Then set all required environment variables:
```bash
# Required
railway variables set JWT_SECRET=$(openssl rand -hex 32)
railway variables set DATABASE_URL=$DATABASE_URL  # Auto-set by Railway Postgres
railway variables set SYNC_DATABASE_URL=$DATABASE_URL_SYNC  # Auto-set by Railway

# OAuth (get from Google/Apple developer consoles)
railway variables set GOOGLE_CLIENT_ID=your-google-client-id
railway variables set APPLE_CLIENT_ID=your-apple-service-id

# WebAuthn (use your Railway domain)
railway variables set WEBAUTHN_RP_ID=your-app.up.railway.app
railway variables set WEBAUTHN_RP_NAME=Adajoon
railway variables set WEBAUTHN_ORIGIN=https://your-app.up.railway.app

# Optional: Stripe for subscriptions
railway variables set STRIPE_SECRET_KEY=sk_live_...
railway variables set STRIPE_WEBHOOK_SECRET=whsec_...
railway variables set STRIPE_PUBLISHABLE_KEY=pk_live_...

# Optional: Analytics
railway variables set MIXPANEL_TOKEN=your-token
railway variables set POSTHOG_API_KEY=phc_...

# Environment
railway variables set ENV=production
```

### 5. Deploy Backend
```bash
railway up
```

### 6. Run Database Migrations
```bash
railway run alembic upgrade head
```

### 7. Deploy Worker (Background Validator)
Create a second service for the worker:
```bash
railway add
# Choose "Empty Service"
# Set start command: python -m app.worker
```

### 8. Deploy Frontend
Option A: Deploy as separate Railway service
```bash
cd frontend
railway init  # Create new project for frontend
railway up
```

Option B: Use Vercel/Netlify for frontend (recommended)
- Frontend should point to your Railway backend URL
- Update VITE_API_URL in frontend/.env

## Architecture on Railway

```
┌─────────────────────────────────────┐
│ Railway Project: Adajoon            │
├─────────────────────────────────────┤
│  Service 1: PostgreSQL (Plugin)     │
│  Service 2: Backend API             │
│  Service 3: Worker (Validator)      │
│  (Service 4: Frontend - Optional)   │
└─────────────────────────────────────┘
```

## Post-Deployment

### Check Logs
```bash
railway logs
```

### Check Database
```bash
railway connect postgres
# Then run SQL queries to verify data
```

### Test API
```bash
curl https://your-app.up.railway.app/api/stats
```

### Monitor Validation
The worker runs continuously validating streams. Check logs:
```bash
railway logs --service worker
```

## Cost Estimate
- Postgres Plugin: ~$5/month
- Backend Service: ~$5/month (512MB RAM)
- Worker Service: ~$5/month (512MB RAM)
- **Total: ~$15-20/month**

## Troubleshooting

### "L 0" and "✓ 0" badges showing zero
This is normal initially. The worker needs 10-30 minutes to validate all channels. Monitor with:
```bash
railway logs --service worker -f
```

Once validation completes, badges will show real counts.

### Database connection errors
Ensure `DATABASE_URL` is set correctly. Railway auto-injects this, but the format must match:
- Backend: `postgresql+asyncpg://user:pass@host:port/db`
- Worker: Same format

### CORS errors
Add your Railway frontend domain to `backend/app/config.py` cors_origins list.
