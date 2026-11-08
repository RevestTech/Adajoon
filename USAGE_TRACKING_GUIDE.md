# Usage & Duration Tracking - Quick Guide

## ✅ Custom Self-Hosted Analytics

Your site now has **custom analytics** that stores all data in your own PostgreSQL database. No third-party services!

### What's Tracking

1. **Session Tracking**
   - Total time on site
   - Active vs idle time
   - Engagement rate
   - Heartbeats every 60 seconds

2. **Playback Tracking**
   - Watch time per channel
   - Listen time per station
   - Heartbeats every 30 seconds
   - Total watch/listen sessions

3. **User Actions**
   - Searches, favorites, votes, shares
   - Login/signup events
   - Filter applications

---

## 📊 How to View Your Data

### Option 1: Admin Dashboard (Quick Overview)

1. Go to https://www.adajoon.com
2. Log in as admin (`khash@khash.com`)
3. Click your avatar → **Admin Dashboard**
4. Navigate to **Analytics** tab (when implemented)

**Currently shows** (in Overview/Activity tabs):
- Active users (24h, 7d, 30d)
- Recently watched content
- User growth over time

**Coming soon**:
- Session duration stats
- Engagement metrics
- Top content by watch time

### Option 2: Direct Database Queries

Connect to your PostgreSQL database and run queries:

#### Daily Active Users
```sql
SELECT DATE(created_at) as date, COUNT(DISTINCT user_id) as users
FROM analytics_events
WHERE event_name = 'Session Started'
AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date;
```

#### Average Session Duration
```sql
SELECT AVG((properties->>'total_duration_seconds')::int) / 60.0 as avg_minutes
FROM analytics_events
WHERE event_name = 'Session Ended'
AND created_at >= NOW() - INTERVAL '7 days';
```

#### Top Channels by Watch Time
```sql
SELECT 
  properties->>'item_name' as channel,
  COUNT(*) as plays,
  SUM((properties->>'total_duration_seconds')::int) / 3600.0 as total_hours
FROM analytics_events
WHERE event_name = 'Playback Session'
AND properties->>'item_type' = 'tv'
AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY properties->>'item_name'
ORDER BY total_hours DESC
LIMIT 10;
```

### Option 3: Admin API (Programmatic Access)

Use the admin API endpoints (requires admin authentication):

```bash
# Get analytics summary
curl -s "https://www.adajoon.com/api/admin/analytics/summary?days=7" \
  --cookie "auth_token=YOUR_TOKEN" | jq .

# Get events over time
curl -s "https://www.adajoon.com/api/admin/analytics/events-over-time?days=30" \
  --cookie "auth_token=YOUR_TOKEN" | jq .

# Get top content
curl -s "https://www.adajoon.com/api/admin/analytics/top-content?days=7&limit=10" \
  --cookie "auth_token=YOUR_TOKEN" | jq .
```

---

## 🎯 Key Metrics

### Daily Metrics
- **DAU (Daily Active Users)**: Unique users per day
- **Sessions**: Total visits per day
- **Avg Session Duration**: Time spent on site
- **Avg Watch Time**: Time watching content

### Weekly/Monthly
- **MAU (Monthly Active Users)**: Unique users per month
- **DAU/MAU Ratio**: Stickiness (ideal: >20%)
- **Retention**: 7-day and 30-day return rates
- **Top Content**: Most watched channels/stations

### Engagement
- **Active Time %**: Time engaged vs idle
- **Watch Time per User**: Average content consumption
- **Sessions per User**: Visit frequency

---

## 🎬 Events Being Tracked

All events are stored in the `analytics_events` table:

### Session Events
- `Session Started` - Page load
- `Session Heartbeat` - Every 60s
- `Session Ended` - Exit with full metrics
- `User Became Active/Idle` - Activity state
- `Tab Hidden/Visible` - Tab switching

### Playback Events
- `Playback Started` - Start watching/listening
- `Playback Heartbeat` - Every 30s
- `Playback Ended` - Stop playback
- `Playback Session` - Full session summary

### User Actions
- `Content Played`, `Search Performed`
- `Favorite Action`, `Vote Cast`
- `Content Shared`, `Filter Applied`
- `User Signed Up`, `User Logged In`

---

## 📈 Sample Queries

### Total Events Today
```sql
SELECT COUNT(*) FROM analytics_events
WHERE DATE(created_at) = CURRENT_DATE;
```

### Most Active Users (Last 7 Days)
```sql
SELECT user_id, COUNT(*) as events
FROM analytics_events
WHERE created_at >= NOW() - INTERVAL '7 days'
AND user_id IS NOT NULL
GROUP BY user_id
ORDER BY events DESC
LIMIT 10;
```

### Engagement Rate by Day
```sql
SELECT 
  DATE(created_at) as date,
  AVG((properties->>'engagement_rate')::float) as avg_engagement
FROM analytics_events
WHERE event_name = 'Session Ended'
AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date;
```

### Watch Time by Category
```sql
SELECT 
  properties->>'item_category' as category,
  SUM((properties->>'total_duration_seconds')::int) / 3600.0 as total_hours
FROM analytics_events
WHERE event_name = 'Playback Session'
AND properties->>'item_type' = 'tv'
AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY properties->>'item_category'
ORDER BY total_hours DESC;
```

---

## 🔧 Database Access

### Via Railway Dashboard

1. Go to https://railway.app
2. Select Adajoon project
3. Click on **Postgres** service
4. Click **Data** tab to browse tables
5. Use **Query** tab to run SQL

### Via psql (Command Line)

```bash
# Get connection string from Railway
railway variables -s backend | grep DATABASE_URL

# Connect
psql "postgresql://user:pass@host:port/database"

# Query
SELECT * FROM analytics_events ORDER BY created_at DESC LIMIT 10;
```

---

## 🗄️ Data Retention

### Storage Estimates

- **Per event**: ~500 bytes
- **100K events/day**: ~50MB/day (~1.5GB/month)
- **1M events**: ~500MB

### Cleanup Old Data (Recommended)

Keep last 90 days, archive older events:

```sql
-- Delete events older than 90 days
DELETE FROM analytics_events
WHERE created_at < NOW() - INTERVAL '90 days';
```

**Or archive instead**:
```sql
-- Create archive table (one-time)
CREATE TABLE analytics_events_archive (LIKE analytics_events INCLUDING ALL);

-- Move old data
INSERT INTO analytics_events_archive
SELECT * FROM analytics_events
WHERE created_at < NOW() - INTERVAL '90 days';

DELETE FROM analytics_events
WHERE created_at < NOW() - INTERVAL '90 days';
```

---

## 🔒 Privacy & GDPR

### Data Collected

- User ID (only for logged-in users)
- IP address (backend adds automatically)
- User agent (browser info)
- Event properties (pages visited, content watched)

### User Rights

**Right to Access**:
```sql
SELECT * FROM analytics_events WHERE user_id = 123;
```

**Right to Delete**:
```sql
DELETE FROM analytics_events WHERE user_id = 123;
```

**Right to Opt-Out**:
Add a toggle in user settings to disable tracking.

---

## 📚 Full Documentation

For complete technical details:
- **Read**: `docs/CUSTOM_ANALYTICS.md`
- **API Reference**: All endpoints and schemas
- **SQL Queries**: Advanced analytics queries
- **Performance**: Optimization tips

---

## 🚀 Next Steps

1. **Run the migration**: `alembic upgrade head`
2. **Start tracking**: Analytics are now live!
3. **View your data**: Check admin dashboard or run SQL queries
4. **Set up retention**: Schedule cleanup of old events
5. **Build custom reports**: Query database for specific insights

---

**Tracking since**: April 12, 2026  
**Storage**: Your own PostgreSQL database  
**Privacy**: 100% self-hosted, no third-party services  
**Status**: ✅ Live in production
