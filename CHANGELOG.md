# Changelog

All notable changes to Adajoon will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.6.0] - 2026-07-21

### Added
- **Radio world map**: MapLibre explorer (Map → Radio Stations) with bbox clusters/pins, Take a ride, geo sync from Radio Browser
- **TV EPG**: `epg_programmes` table, worker XMLTV ingest, `/api/epg/now` + channel schedule APIs, VideoPlayer now/next strip
- **AI on-now sports**: Keyword/AI TV search merges EPG programmes airing now for soccer/football/fifa-style queries
- **Radio browser-window pop-out**: Desktop “Open in new window” opens a dedicated popup player (`RadioPopoutWindow`)
- **Auth funnel + path analytics**: Client and server emit login attempt/success/failure/session-lost; screen + navigation tracking; Admin Analytics shows funnel, recent failures, top screens/navigations (`/api/admin/analytics/auth-funnel`, `/paths`)
- See `docs/RADIO_MAP_EPG.md`, `docs/FLOATING_PLAYER.md`, `docs/CUSTOM_ANALYTICS.md`

### Fixed
- **Login / cookie reliability**: Adaptive cookie domain (Railway host vs `.adajoon.com`); WebAuthn multi-origin list; Apple `postMessage` single origin; CSRF header attached on authenticated fetches; softer `/me` logout
- **Channel schema 500s**: Coerce ORM `None`/`datetime` timestamps on `ChannelOut` / `RadioStationOut`
- **CSP for IPTV + MapLibre**: `media-src` allows `http:`; `worker-src blob:` and OpenFreeMap hosts for the radio map
- **Map bbox at world zoom**: Clamp longitudes outside ±180 instead of returning 400
- **Dark map contrast**: Lighten OpenFreeMap dark basemap paints; stub missing style sprites (`circle-11`)

### Added (carried from earlier unreleased)
- **Floating Player (Desktop Only)**: Pop-out player for TV channels and radio stations
- **Custom Self-Hosted Analytics**: PostgreSQL-backed tracking (sessions, playback, actions); Admin `/api/admin/analytics/*`
- **Admin Dashboard**: User/content/activity stats; admin-only via avatar menu

### Removed
- **Mixpanel / PostHog**: Replaced by self-hosted analytics (`docs/CUSTOM_ANALYTICS.md`)

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
