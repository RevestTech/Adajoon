# Radio Map & TV EPG

Feature reference for the radio.garden-style world map and electronic program guide (EPG).

## Radio world map

### User experience

1. Open **Map** mode → **Radio Stations**
2. Pan/zoom a MapLibre basemap (OpenFreeMap dark style with contrast boosts)
3. Green **clusters** at low zoom; individual **station pins** at higher zoom
4. Click a pin to play in the in-app radio player
5. **Take a ride** picks a random playable geo station near the map center

TV choropleth map remains available under **Map → TV Channels**.

### Backend

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/radio/map?bbox=west,south,east,north&zoom=&limit=&working_only=` | Stations or grid clusters in viewport |
| GET | `/api/radio/map/ride?lat=&lng=&working_only=` | Random playable geo station (404 if none) |

- `zoom <= 7` → `{ type: "clusters", items: [{ lat, lng, count }], zoom }`
- `zoom >= 8` → `{ type: "stations", items: [{ id, name, favicon, geo_lat, geo_long, country_code }], zoom }`
- Bbox longitudes outside ±180 are **clamped** (MapLibre world views often exceed the range)
- Geo fields are populated during `sync_radio_stations` from Radio Browser (`geo_lat` / `geo_long`)

### Frontend

- `frontend/src/components/RadioGardenMap.jsx` (+ CSS)
- API helpers: `fetchRadioMap`, `fetchRadioMapRide` in `frontend/src/api/radio.js`
- Style URL: `VITE_MAP_STYLE_URL` or default `https://tiles.openfreemap.org/styles/dark`
- Dependency: `maplibre-gl`

### CSP (production)

MapLibre needs these directives (see `backend/app/middleware/security_headers.py`):

- `worker-src 'self' blob:`
- `connect-src` … `https://tiles.openfreemap.org`
- `font-src` … `https://tiles.openfreemap.org`
- `img-src` includes `blob:` and `https:`

### Notes

- Empty map items until radio sync has written geo coordinates
- Third-party station favicons may fail with CORP/`402` — UI falls back; playback is unaffected

---

## TV EPG

### Data model

Table `epg_programmes` (Alembic `011_add_epg_programmes`):

- `channel_id`, `start_at`, `stop_at`, `title`, `subtitle`, `description`, `category`
- Indexes for schedule and “on now” queries

### Ingest (worker)

- `backend/app/services/epg_service.py` → `sync_epg`
- Wired in `backend/app/worker.py` after radio sync
- Env:
  - `EPG_COUNTRY_CODES` (default `us,uk,de`)
  - `EPG_BASE_URL` (default `https://iptv-org.github.io/epg/guides` — may 404; set a working mirror)
  - `EPG_PRUNE_DAYS` (default `2`)
- Per-country failures are isolated; sync continues

### APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/channels/{id}/epg?from=&to=` | Schedule window (default now → +24h) |
| GET | `/api/epg/now?channel_id=` | Current + next programme |
| GET | `/api/epg/now?q=` / `category=` | Programmes airing now matching title/category |

### Frontend

- Now/next strip in `VideoPlayer.jsx` via `frontend/src/api/epg.js`
- ChannelGrid “on now” badge deferred (no batch endpoint)

### AI search

Sports-style queries (soccer, football, fifa, …) merge EPG **on-now** hits ahead of name/category fallback (`ai_search_service.py`). Sources: `ai+epg` / `fallback+epg`. Empty EPG does not fail search.

---

## Radio browser-window pop-out

Desktop **Open in new window** on the radio player opens `/?radio_popout=1&sid=…` in a real browser popup (`RadioPopoutWindow.jsx`). Station payload is stashed in `localStorage` briefly. Main-window audio stops to avoid double play. If the popup is blocked, the in-app floating player is used as fallback.

See also `docs/FLOATING_PLAYER.md`.
