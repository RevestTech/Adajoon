# Changelog

All notable changes to Adajoon will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Floating Player (Desktop Only)**: Pop-out player for TV channels and radio stations
  - Draggable window that stays on top while browsing
  - Resizable from 280x160 to 800x600 pixels
  - Dock back to main player with one click
  - Position and size preferences saved locally
  - Keyboard shortcut support (Escape to close)
  - Only available on desktop devices (not mobile/TV)
  - Accessible via "Pop Out" button in video/radio player controls

- **Custom Self-Hosted Analytics**: Full replacement of Mixpanel with database-backed tracking
  - All events stored in PostgreSQL (`analytics_events` table)
  - No third-party dependencies or data sharing
  - Session tracking (total, active, idle time with 60s heartbeats)
  - Playback tracking (30s heartbeats per channel/station)
  - User action tracking (searches, favorites, votes, shares)
  - Admin API endpoints for analytics queries (`/api/admin/analytics/*`)
  - Batch event submission for performance (5s intervals)
  - JSONB properties for flexible event data
  - See `docs/CUSTOM_ANALYTICS.md` for full reference

- **Admin Dashboard**: Real-time statistics and user management
  - User counts by provider (Google, Apple, Passkey)
  - Active users (24h, 7d, 30d)
  - System health monitoring (database, Redis, uptime)
  - Content statistics (channels, stations, categories)
  - Recent activity timeline
  - User management (promote/revoke admin)
  - Only visible to admin users (`is_admin` flag)
  - Accessible via user avatar dropdown menu

### Removed
- **Mixpanel Integration**: Removed third-party analytics service
  - Removed `mixpanel-browser` dependency
  - Removed PostHog integration
  - Replaced with custom self-hosted analytics
  - All existing event tracking migrated to new system

## [2.5.2] - 2026-04-07

### Fixed
- **Black screen on iOS Safari (iPhone)**: Removed `height: -webkit-fill-available` from `#root` which computed to 0 on certain iOS Safari versions, clipping all content. Replaced with standard `100vh` + `100dvh` fallback
- **Stale HTML cached on mobile**: Nginx `Cache-Control: no-cache` only applied to `location = /index.html` but not when served via `try_files` fallback from `location /`. Added aggressive no-cache headers (`no-store, must-revalidate`) to the catch-all location block
- **External scripts blocking iOS rendering**: Made Chromecast SDK and Google IMA SDK scripts `async defer` to prevent parser-blocking on iOS Safari
- **CSS `dvh` units without fallback**: Added `vh` fallbacks before all `dvh` declarations in sidebar and modal mobile styles

### Added
- Inline loading fallback ("Loading Adajoon...") in `index.html` visible until React mounts
- Inline `window.onerror` handler that displays JavaScript errors visually for debugging
- Server-side non-www to www redirect in nginx config (`return 301`)

## [2.5.1] - 2026-04-07

### Fixed
- **502 Bad Gateway on all API calls**: Frontend nginx proxy was defaulting to port 8000 but Railway runs the backend on port 8080. Updated `frontend/start.sh` default `BACKEND_URL` from `http://backend:8000` to `http://backend.railway.internal:8080`
- **Nginx proxy template**: Added `proxy_connect_timeout 10s` to `/api/` location block in `nginx.conf.template` for better error handling

### Changed
- **Railway service cleanup**: Renamed frontend service from "Adajoon" back to "frontend" for consistency with codebase conventions
- **Backend CORS origins**: Added `https://adajoon-production.up.railway.app` to `CORS_ORIGINS` and `WEBAUTHN_ORIGIN` environment variables

### Removed
- Deleted orphaned "frontend" service (had failed deployment from earlier rebuild)
- Deleted accidental "function-bun" service (created by Railway Agent intercepting keyboard input)

## [2.5.0] - 2026-04-05

### Added
- **Smart TV Support**: Full optimization for Samsung Tizen, LG webOS, and other TV browsers
  - Automatic device detection for TV platforms
  - 10-foot UI with larger text (24px base) and buttons (60px min height)
  - D-pad navigation support for TV remote controls
  - Samsung/LG back button handling
  - Enhanced focus indicators (4px white outline with glow)
  - TV-safe zones (5% padding from screen edges)
  - TV Mode debug indicator badge
- Device detection utilities (`deviceDetection.js`)
- TV-specific React hooks (`useDevice`, `useTVNavigation`)
- TV-optimized CSS styles (`tv.css`, `tv-debug.css`)
- Comprehensive TV optimization documentation (`docs/TV_OPTIMIZATION.md`)

### Changed
- Updated Vite build target to ES2015 for TV browser compatibility
- Set CSS target to Chrome 61 for older smart TV browsers
- Improved browser compatibility for Samsung Tizen 2.4+ (2017+ models)

### Fixed
- Blank screen issue on Samsung Internet browser (JavaScript compatibility)
- Remote control navigation not working on TV devices

## [2.4.0] - 2026-04-04

### Added
- Enhanced voting system for TV channels and radio stations
- Recently played history tracking
- Guest mode with local favorites
- Improved authentication flow

### Changed
- Modernized UI with updated color scheme
- Improved mobile responsiveness
- Enhanced video player controls

### Fixed
- Various bug fixes and performance improvements

## [2.3.0] - 2026-03-15

### Added
- Radio station streaming support
- Category and country filtering
- Quality indicators for streams
- Favorites synchronization

### Changed
- Improved search functionality
- Enhanced sidebar navigation
- Better error handling

## [2.2.0] - 2026-02-20

### Added
- OAuth authentication (Google, Apple)
- Passkey/WebAuthn support
- User profile management
- CSRF protection

### Changed
- Updated security headers
- Improved cookie handling
- Enhanced CORS configuration

## [2.1.0] - 2026-01-15

### Added
- Initial public release
- Live TV channel streaming
- HLS video player
- Basic search and filtering

---

## Version Numbering

- **Major version** (X.0.0): Breaking changes, major feature overhauls
- **Minor version** (0.X.0): New features, backward compatible
- **Patch version** (0.0.X): Bug fixes, minor improvements

## Links

- [GitHub Repository](https://github.com/yourusername/adajoon)
- [Documentation](./docs/)
- [TV Optimization Guide](./docs/TV_OPTIMIZATION.md)
