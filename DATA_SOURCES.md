# Adajoon Data Sources

## Overview
Adajoon aggregates streaming content from two major open-source projects, providing access to thousands of TV channels and radio stations worldwide.

## TV Channels - IPTV.org

**Source**: [IPTV.org](https://github.com/iptv-org/iptv)
**API**: `https://iptv-org.github.io/api/` (inferred from code structure)

### What is IPTV.org?
IPTV.org is a massive community-driven collection of publicly available IPTV (Internet Protocol Television) channels from around the world. It's one of the largest open databases of legal streaming TV channels.

### What we fetch:
- **Categories** (`/categories.json`) - News, Sports, Entertainment, Music, etc.
- **Countries** (`/countries.json`) - All countries with available channels
- **Languages** (`/languages.json`) - Supported broadcast languages
- **Channels** (`/channels.json`) - Channel metadata (name, network, logo, etc.)
- **Streams** (`/streams.json`) - Actual streaming URLs for each channel

### Data Points per Channel:
- Name & Alternative Names
- Network/Broadcaster
- Country & Languages
- Categories (News, Sports, etc.)
- Logo URL
- Official Website
- Stream URLs (HLS/M3U8)
- Broadcast Area
- NSFW flag
- Closed Caption support

### Scale:
- **~10,000+ TV channels** from 200+ countries
- Multiple streams per channel (backup URLs)
- Regular updates from the community

## Radio Stations - Radio Browser

**Source**: [Radio Browser](https://www.radio-browser.info/)
**API**: `https://de1.api.radio-browser.info`

### What is Radio Browser?
Radio Browser is a community-driven, open-source project that catalogs internet radio stations worldwide. It's the largest free database of radio station streams.

### What we fetch:
We query the Radio Browser API with these parameters:
- `limit: 10,000` per batch
- `offset: 0, 10000, 20000, ...` for pagination
- `order: votes` - sorted by popularity
- `reverse: true` - most voted first
- `hidebroken: true` - only working stations
- **Max: 50,000 stations** (top rated)

### Data Points per Station:
- Name
- Stream URL (direct & resolved)
- Homepage & Favicon
- Tags (genre, style, etc.)
- Country, Country Code & State
- Language
- Codec (MP3, AAC, etc.)
- Bitrate (quality)
- Vote count (popularity)
- Last check status

### Scale:
- **50,000 top radio stations** (from ~70,000+ total)
- Sorted by community votes for quality
- Real-time availability checking
- Multiple languages and genres

## Data Sync Process

### Automated Worker
Our background worker (`backend/app/worker.py`) runs every hour and:

1. **Validates Channels** - Tests all TV channel streams for availability
2. **Validates Radio** - Tests all radio station streams
3. **Syncs IPTV Data** - Fetches latest channels from IPTV.org
4. **Syncs Radio Data** - Fetches top stations from Radio Browser

### Validation System
Every stream is tested to verify:
- **HTTP Response** - Does the URL respond?
- **HLS Playlist** - Can we parse the M3U8 manifest?
- **Status Mapping**:
  - `verified` - Stream works, HLS parsed successfully
  - `online` - Stream responds but may not be HLS
  - `offline` - Stream is unavailable

### Health Tracking
For each channel/station we store:
- `health_status` - Current working status
- `health_checked_at` - Last validation timestamp
- This data powers the "L" (Live) and "✓" (Verified) badges in the UI

## Database Storage

All synced data is stored in PostgreSQL with:
- **Bulk inserts** (500 records at a time) for performance
- **Upsert logic** - Update if exists, insert if new
- **Batched writes** - Prevents memory issues
- **Efficient indexing** - Fast search and filtering

## Data Quality

### IPTV.org Channels:
- Community maintained and verified
- Legal, publicly available streams
- Regular community contributions
- Dead streams removed by maintainers

### Radio Browser Stations:
- Top 50K by votes ensures quality
- `hidebroken: true` excludes dead streams
- Active community reporting
- Automatic health checking

## Why These Sources?

1. **Open & Free** - No licensing fees or API limits
2. **Community Driven** - Thousands of contributors maintaining data
3. **Global Coverage** - Content from every corner of the world
4. **Legal & Public** - Only publicly available, legal streams
5. **Well Maintained** - Active communities updating daily
6. **API Accessible** - Easy programmatic access
7. **Rich Metadata** - Detailed information for great UX

## Attribution

Adajoon stands on the shoulders of giants:
- **IPTV.org** - https://github.com/iptv-org/iptv
- **Radio Browser** - https://www.radio-browser.info/

These projects make global streaming accessible to everyone. We validate, enhance, and present their data through a beautiful, user-friendly interface.
