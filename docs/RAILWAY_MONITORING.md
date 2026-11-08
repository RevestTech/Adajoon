# Railway Monitoring & Analytics

## Overview

Adajoon uses a combination of Railway infrastructure monitoring, application-level analytics, and a custom admin dashboard to track usage and performance.

## Infrastructure Monitoring (Railway)

### What Railway Provides

Railway automatically monitors infrastructure-level metrics for your services:

#### 1. **Service Metrics** (Available in Railway Dashboard)
- **CPU Usage**: Percentage of allocated CPU being used
- **Memory Usage**: RAM consumption (MB/GB)
- **Network I/O**: Inbound/outbound bandwidth
- **Disk Usage**: Storage consumption

#### 2. **Deployment Metrics**
- Build times and success rates
- Deployment frequency
- Service uptime and availability

#### 3. **Logs**
- Structured application logs (JSON format when `JSON_LOGS=true`)
- Error tracking and debugging
- Request/response logs

### Accessing Railway Metrics

1. **Railway Dashboard**: https://railway.app/dashboard
   - Select your project
   - Click on each service (backend, frontend, worker)
   - View **"Metrics"** tab for real-time graphs

2. **Observability Tab**: 
   - Aggregated metrics across all services
   - Alert configuration for high CPU/memory
   - Deployment history

3. **CLI Monitoring**:
   ```bash
   railway logs --service backend
   railway logs --service frontend
   ```

### Railway Does NOT Track:
- Application-level user behavior (pages viewed, features used)
- Business metrics (signups, conversions, revenue)
- User demographics or preferences
- Custom events (video plays, searches, etc.)

---

## Application-Level Analytics

### 1. Self-hosted analytics (PostgreSQL)

**Setup**: `frontend/src/analytics.js` → `POST /api/analytics/batch` → `analytics_events`

**What It Tracks**:
- Sessions (start / heartbeat / end, idle vs active)
- Channel/station playback heartbeats
- Searches, favorites, votes, shares, filters
- **Auth funnel**: attempt / success / failure / session lost (client + server)
- **Paths**: `Screen View` and `Navigation` (mode, map, favorites, player, login, …)

**Viewing Data**:
- Admin → **Analytics** tab (summary, auth funnel, top screens/navigations, top content)
- APIs: `/api/admin/analytics/summary`, `auth-funnel`, `paths`, `top-content`, `events-over-time`
- Full reference: [`docs/CUSTOM_ANALYTICS.md`](CUSTOM_ANALYTICS.md)

### 2. Prometheus Metrics (Backend)

**Endpoint**: `/metrics` (internal use only)

**What It Exposes**:
- HTTP request counts and latency
- Database query performance
- Redis connection pool stats
- Active request gauge

**Viewing Metrics**:
```bash
curl https://adajoon.com/metrics
```

---

## Custom Admin Dashboard

### Features

The admin dashboard (`/admin`) provides:

#### 1. **User Statistics**
- Total registered users
- Active users (last 7 days)
- New signups (last 30 days)
- Admin count
- Paid vs free users
- Daily signup trends
- Users by OAuth provider (Google, Apple, Passkey)
- Users by subscription tier

#### 2. **Content Statistics**
- Total TV channels and radio stations
- Most favorited channels/stations
- Content health status distribution
- Top performing content

#### 3. **Activity Metrics**
- Watches this week
- Total favorites, votes, playlists
- Daily watch trends (TV vs Radio)
- Vote distribution by type
- Playlist creation trends

#### 4. **System Health**
- Database connectivity
- Redis status
- Recent errors
- API response times

### Accessing the Admin Dashboard

1. **Get Admin Access**:
   - First user: Manually set in database
   ```sql
   UPDATE users SET is_admin = true, role = 'admin' WHERE email = 'your@email.com';
   ```
   
   - Additional admins: Use the "Make Admin" feature in the dashboard

2. **Visit**: https://adajoon.com/admin
   - Requires authentication
   - Redirects non-admins with 403 Forbidden

### API Endpoints (Admin Only)

All endpoints require `is_admin = true`:

- `GET /api/admin/stats/overview` - High-level metrics
- `GET /api/admin/stats/users?days=30` - Detailed user analytics
- `GET /api/admin/stats/content` - Content performance
- `GET /api/admin/stats/activity?days=30` - User engagement
- `GET /api/admin/analytics/summary?days=7` - Event summary
- `GET /api/admin/analytics/auth-funnel?days=7` - Login success vs failure
- `GET /api/admin/analytics/paths?days=7` - Top screens / navigations
- `GET /api/admin/analytics/top-content?days=7` - Most played content
- `POST /api/admin/users/{user_id}/make-admin` - Grant admin
- `POST /api/admin/users/{user_id}/revoke-admin` - Revoke admin

---

## Recommended Monitoring Strategy

### For Daily Checks
1. **Railway Dashboard**: Quick glance at CPU/memory/errors
2. **Admin Dashboard**: User growth and engagement trends
3. **Auth Funnel**: Login attempt / success / failure rates

### For Weekly Reviews
1. **Admin Stats**: Weekly active users, new signups
2. **Content Performance**: Top channels, dead links
3. **Auth Funnel / Paths**: Login success vs failure; top screens (Admin → Analytics)

### For Monthly Planning
1. **Growth Metrics**: Month-over-month user growth
2. **Subscription Trends**: Free → paid conversion rate
3. **Feature Usage**: Most/least used screens and navigations (self-hosted analytics)
4. **Infrastructure Costs**: Railway usage and scaling needs

---

## Setting Up Alerts

### Railway Alerts
1. Go to Project Settings → Alerts
2. Configure:
   - CPU > 80% for 5 minutes
   - Memory > 90% for 5 minutes
   - Deployment failures

### Auth / product alerts
1. Watch Admin → Analytics → Auth Funnel for spike in `Auth Login Failed`
2. Review recent failures table for method + error text
3. Cross-check Railway logs for `/api/auth/*` 4xx/5xx

### Custom Alerts (Future)
Consider adding:
- Sentry for error tracking
- UptimeRobot for availability monitoring
- PagerDuty for incident response

---

## Admin Dashboard Setup Guide

### 1. Database Migration
```bash
cd backend
alembic upgrade head  # Applies migration 009 (admin roles)
```

### 2. Make First Admin
Connect to production database:
```bash
railway run psql $DATABASE_URL
```

Then run:
```sql
UPDATE users 
SET is_admin = true, role = 'admin' 
WHERE email = 'your.admin@email.com';
```

### 3. Access Dashboard
- Navigate to https://adajoon.com/admin
- Login with your admin account
- View all metrics and manage users

---

## Security Considerations

### Admin Access
- Admin routes protected by `require_admin` middleware
- Returns 403 Forbidden for non-admin users
- Tracks all admin actions in logs

### Data Privacy
- User emails visible to admins (for management)
- No passwords stored (OAuth only)
- Sensitive data masked in logs

### Best Practices
- Limit admin accounts to 2-3 trusted users
- Use separate admin account (not personal)
- Review admin logs weekly for suspicious activity
- Revoke admin access when team members leave

---

## Troubleshooting

### "Railway metrics not showing"
- Check service is running (green status)
- Wait 5-10 minutes for initial metrics
- Verify project has active deployments

### "Admin dashboard returns 403"
- Confirm `is_admin = true` in database
- Clear browser cookies and re-login
- Check backend logs for authentication errors

### "Analytics events not appearing"
- Open Network tab → `/api/analytics/batch`
- Confirm Admin → Analytics shows recent events
- Query `SELECT COUNT(*) FROM analytics_events;`
- Check backend logs for analytics insert errors

---

## Version
- **Created**: 2026-04-12
- **Last Updated**: 2026-07-21 (v2.6.0 — self-hosted auth funnel + paths)
- **Admin Dashboard**: Auth funnel + path analytics
