# Admin Dashboard - Access Guide

## ✅ Setup Complete!

Your admin dashboard is now fully configured and deployed on Railway.

## How to Access

1. **Log in to Adajoon** at https://www.adajoon.com
   - Use your Google, Apple, or Passkey login
   - Your account: `khash@khash.com`

2. **Click your avatar** in the top-right corner

3. **Click "Admin Dashboard"** in the dropdown menu
   - This button only appears for admin users
   - If you don't see it, try logging out and back in to refresh your session

## What You Can See

The admin dashboard provides real-time statistics across 4 tabs:

### Overview Tab
- Total users (by provider: Google, Apple, Passkey)
- Active users (last 24h, 7d, 30d)
- TV channels and radio stations count
- System health (database, Redis, uptime)
- Recent activity timeline

### Users Tab
- User growth over time (bar chart)
- Provider distribution
- Recent signups (last 10)

### Content Tab
- Most popular channels
- Category distribution
- Parental control stats

### Activity Tab
- Recently watched content
- Active users timeline
- Peak usage hours

## API Endpoints

All admin endpoints require authentication (logged in as admin):

```
GET /api/admin/stats/overview
GET /api/admin/stats/users?days=30
GET /api/admin/stats/content
GET /api/admin/stats/activity?days=7
POST /api/admin/users/{user_id}/make-admin
POST /api/admin/users/{user_id}/revoke-admin
```

## Railway Monitoring

For infrastructure monitoring (CPU, memory, network):
- Go to https://railway.app
- Select your Adajoon project
- View metrics for each service (backend, frontend, Postgres, Redis)

See `docs/RAILWAY_MONITORING.md` for comprehensive monitoring strategy.

## Security

- Admin role is stored in the database (`is_admin` column)
- Backend middleware enforces admin-only access
- Frontend UI conditionally shows admin features
- All admin API calls require authentication via session cookie

## Next Steps

- Set up monitoring alerts in Railway for critical issues
- Configure Mixpanel/PostHog for user behavior analytics
- Consider adding more admin features (user management, content moderation)

---

**Last updated:** April 12, 2026  
**Admin configured:** khash@khash.com  
**Status:** ✅ Live in production
