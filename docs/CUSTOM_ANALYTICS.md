# Custom Self-Hosted Analytics

Adajoon uses a **custom self-hosted analytics system** that stores all events in your own PostgreSQL database. No third-party services required!

## Overview

All analytics data is:
- ✅ **Stored in your database**: Full data ownership
- ✅ **Queried via admin dashboard**: No external tools needed
- ✅ **Tracked in real-time**: Events batched and sent every 5 seconds
- ✅ **Privacy-friendly**: No data sent to third parties

---

## Architecture

### Frontend → Backend → Database

```
User Action → analytics.track() → Event Queue (frontend)
                                        ↓
                                  Batch every 5s
                                        ↓
                          POST /api/analytics/batch
                                        ↓
                            PostgreSQL (analytics_events table)
                                        ↓
                        Admin Dashboard (queries & reports)
```

---

## Database Schema

### `analytics_events` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `user_id` | INTEGER | User ID (NULL for guests) |
| `session_id` | VARCHAR(255) | Unique session identifier |
| `event_name` | VARCHAR(100) | Event type (e.g., "Page View") |
| `properties` | JSONB | Event metadata |
| `created_at` | TIMESTAMPTZ | Timestamp |

**Indexes**:
- `user_id`, `session_id`, `event_name`, `created_at`
- Composite indexes for common queries

---

## Events Tracked

### Session Events
- `Session Started` - Page load
- `Session Heartbeat` - Every 60s
- `Session Ended` - Page unload
- `User Became Active/Idle` - Activity state changes
- `Tab Hidden/Visible` - Tab switching

### Playback Events
- `Playback Started` - Start watching/listening
- `Playback Heartbeat` - Every 30s while playing
- `Playback Ended` - Stop playback
- `Playback Session` - Full session summary

### User Actions
- `User Signed Up` / `User Logged In`
- `Content Played`, `Search Performed`
- `Favorite Action`, `Vote Cast`
- `Content Shared`, `Filter Applied`

---

## Frontend API

### Track an Event

```javascript
import { analytics } from './analytics';

analytics.track('Button Clicked', {
  button_name: 'Subscribe',
  location: 'header',
});
```

### Track User Login

```javascript
analytics.trackLogin('google', userId);
```

### Track Content Play

```javascript
analytics.trackPlay('tv', channel);
```

### Helper Methods

- `analytics.identify(userId, traits)` - Identify user
- `analytics.page(pageName, properties)` - Track page view
- `analytics.reset()` - Clear session (on logout)
- `analytics.trackSignup(method, userId)`
- `analytics.trackLogin(method, userId)`
- `analytics.trackPlay(itemType, item)`
- `analytics.trackSearch(query, resultCount, itemType)`
- `analytics.trackFavorite(action, itemType, item)`
- `analytics.trackVote(voteType, itemType, item)`
- `analytics.trackShare(method, itemType, item)`
- `analytics.trackFilter(filterType, filterValue, itemType)`

---

## Backend API

### POST `/api/analytics/track`

Track a single event.

**Request**:
```json
{
  "event_name": "Button Clicked",
  "session_id": "1234567890-abc123",
  "properties": {
    "button_name": "Subscribe",
    "location": "header"
  }
}
```

**Response**:
```json
{
  "status": "ok",
  "event_id": 12345
}
```

### POST `/api/analytics/batch`

Track multiple events (preferred for performance).

**Request**:
```json
[
  {
    "event_name": "Page View",
    "session_id": "1234567890-abc123",
    "properties": { "page": "Home" }
  },
  {
    "event_name": "Button Clicked",
    "session_id": "1234567890-abc123",
    "properties": { "button_name": "Subscribe" }
  }
]
```

**Response**:
```json
{
  "status": "ok",
  "events_tracked": 2
}
```

---

## Admin Dashboard API

### GET `/api/admin/analytics/summary?days=7`

Get analytics summary for specified period.

**Response**:
```json
{
  "period_days": 7,
  "total_events": 15234,
  "unique_sessions": 1234,
  "unique_users": 567,
  "avg_session_duration_seconds": 180,
  "top_events": [
    { "event_name": "Page View", "count": 5000 },
    { "event_name": "Playback Started", "count": 2000 }
  ]
}
```

### GET `/api/admin/analytics/events-over-time?days=7`

Get daily event counts.

**Response**:
```json
[
  { "date": "2026-04-05", "count": 2000 },
  { "date": "2026-04-06", "count": 2500 },
  { "date": "2026-04-07", "count": 3000 }
]
```

### GET `/api/admin/analytics/top-content?days=7&limit=10`

Get most popular content.

**Response**:
```json
[
  { "item_name": "BBC News", "item_type": "tv", "play_count": 500 },
  { "item_name": "CNN Live", "item_type": "tv", "play_count": 350 }
]
```

---

## Performance

### Frontend
- **Batching**: Events queued and sent every 5 seconds
- **Async**: Non-blocking, doesn't impact UI performance
- **Lightweight**: ~5KB total overhead
- **Session Storage**: Persistent session ID across page loads

### Backend
- **Bulk Inserts**: Batch endpoint for multiple events
- **Indexed Queries**: Fast lookups on user_id, session_id, event_name
- **JSONB**: Efficient storage of event properties
- **Time-based Partitioning**: Optional for high-volume sites

### Database
- **Table Size**: ~500 bytes per event
- **100K events/day**: ~50MB/day (~1.5GB/month)
- **Retention**: Consider archiving old events (90+ days)

---

## Queries & Reports

### Daily Active Users

```sql
SELECT DATE(created_at) as date, COUNT(DISTINCT user_id) as dau
FROM analytics_events
WHERE event_name = 'Session Started'
AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date;
```

### Average Session Duration

```sql
SELECT AVG(
  (properties->>'total_duration_seconds')::int
) as avg_duration_seconds
FROM analytics_events
WHERE event_name = 'Session Ended'
AND created_at >= NOW() - INTERVAL '7 days';
```

### Top Channels by Watch Time

```sql
SELECT 
  properties->>'item_name' as channel,
  SUM((properties->>'total_duration_seconds')::int) as total_seconds
FROM analytics_events
WHERE event_name = 'Playback Session'
AND properties->>'item_type' = 'tv'
AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY properties->>'item_name'
ORDER BY total_seconds DESC
LIMIT 10;
```

---

## Data Retention

### Automatic Cleanup (Recommended)

Add a cron job to delete old events:

```sql
DELETE FROM analytics_events
WHERE created_at < NOW() - INTERVAL '90 days';
```

### Archive Instead of Delete

```sql
-- Create archive table
CREATE TABLE analytics_events_archive (LIKE analytics_events INCLUDING ALL);

-- Move old data
INSERT INTO analytics_events_archive
SELECT * FROM analytics_events
WHERE created_at < NOW() - INTERVAL '90 days';

DELETE FROM analytics_events
WHERE created_at < NOW() - INTERVAL '90 days';
```

---

## Privacy & GDPR

### User Data

Events store:
- User ID (for logged-in users only)
- IP address (automatically added by backend)
- User agent (browser info)
- Event properties (content viewed, actions taken)

### GDPR Compliance

**Right to Access**:
```sql
SELECT * FROM analytics_events WHERE user_id = ?;
```

**Right to Deletion**:
```sql
DELETE FROM analytics_events WHERE user_id = ?;
```

**Right to Opt-Out**:
```javascript
// In frontend, set flag to disable tracking
localStorage.setItem('analytics_opt_out', 'true');

// Check before sending events
if (localStorage.getItem('analytics_opt_out') === 'true') {
  return; // Don't track
}
```

---

## Migration from Mixpanel

The analytics.js API is **compatible** with the old Mixpanel implementation:

- ✅ Same function names (`track`, `identify`, `page`, etc.)
- ✅ Same event names (`Session Started`, `Playback Started`, etc.)
- ✅ Same properties structure
- ✅ Drop-in replacement (no frontend changes needed)

**Only difference**: Events now go to your database instead of Mixpanel!

---

## Troubleshooting

### Events Not Appearing

1. **Check browser console**: Look for `[Analytics]` logs in dev mode
2. **Check network tab**: Filter for `/api/analytics/batch`
3. **Check database**: `SELECT COUNT(*) FROM analytics_events;`
4. **Check backend logs**: Look for analytics errors

### High Database Load

1. **Increase batch interval**: Change flush timeout from 5s to 10s
2. **Add partitioning**: Partition by created_at (monthly/yearly)
3. **Archive old data**: Move events older than 90 days to archive table

### Session ID Issues

- Session ID is stored in `sessionStorage` (clears on browser close)
- New session ID generated per browser tab
- Use `localStorage` instead if you want persistent cross-tab sessions

---

## Future Enhancements

- [ ] Real-time dashboard updates (WebSocket)
- [ ] Custom event funnels
- [ ] Cohort analysis
- [ ] A/B testing support
- [ ] Automated weekly reports (email)
- [ ] Data export (CSV/JSON)

---

**Version**: 2.6.0  
**Last Updated**: April 12, 2026  
**Migration from Mixpanel**: Complete ✅
