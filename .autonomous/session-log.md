# Session log

## 2026-07-21

- User reported `/api/channels` 500s in browser.
- Confirmed prod: default list 500; `per_page=1` 200; page 2 (`00sReplay.us`) 500.
- Root cause: Pydantic `ChannelOut` str timestamps reject ORM `None`/`datetime`.
- Secondary: CSP blocks `http://` media.
- Started hotfix sprint.

- Deploy SUCCESS 6068dd9c. Smoke: /api/channels 200, 00sReplay.us 200, CSP media-src includes http:.
- All sprint tasks done; loop inactive.
