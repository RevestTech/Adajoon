# Master Plan: Fix /api/channels 500s

**Goal**: Restore production channel listing and playback CSP for HTTP IPTV streams.

## Problem

- `GET /api/channels?page=1&per_page=40` → 500 (browse broken)
- Isolated to rows that fail `ChannelOut` validation (e.g. `00sReplay.us`)
- Root cause: `health_checked_at` / `last_validated_at` are `DateTime | None` in ORM but `str` in Pydantic; `None` and `datetime` raise ValidationError → FastAPI 500
- Secondary: CSP `media-src` allows only `https:`, blocking `http://` HLS streams (e.g. 100automoto)

## Out of scope

- Browser extension "message channel closed" errors
- External icon 402 (reyfm.de)
- apple-touch-icon CORP noise

## Tasks

1. Fix `ChannelOut` / `RadioStationOut` datetime/None coercion
2. Allow `http:` in CSP `media-src` for IPTV
3. Add/adjust unit tests for schema coercion
4. Deploy backend + smoke `/api/channels`
