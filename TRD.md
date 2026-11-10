# Technical Reference

## Stack & versions
- **Backend**: FastAPI 0.135, SQLAlchemy 2.0 (async), asyncpg 0.30/psycopg2-binary 2.9 (two drivers pinned — see Known tech debt in `MASTER_PLAN.md`), Alembic 1.18, Pydantic 2.12, Redis 5.0 (`hiredis`), Stripe SDK 8.2, APScheduler (sync worker), `python-jose`/`webauthn`/`bcrypt`/`itsdangerous` (auth/CSRF), `slowapi` (rate limiting), `prometheus-fastapi-instrumentator`, pytest 9 + pytest-asyncio 1.4. Full list: `backend/requirements.txt`.
- **Frontend**: React 18.3, Vite 8 + `@vitejs/plugin-react` 6 (Babel-free, Oxc-based React Refresh — these two must move together), react-router-dom 7 (present as a dependency but the app otherwise uses manual `pushState` routing — see PR #71's rationale for not adopting it more broadly), `hls.js` (video), `maplibre-gl` (radio/TV map), `@simplewebauthn/browser` (passkeys), Vitest 4 + happy-dom 20.9. Full list: `frontend/package.json`.
- **Deploy**: Railway, dual-service (backend serves the public domain + proxies to an internal-only frontend/nginx service). See `docs/RAILWAY_MONITORING.md`.

## Data model (`backend/app/models.py`, 20 tables)
`User`, `UserFavorite`, `UserVote`, `WatchHistory`, `Playlist`, `PlaylistItem`, `Passkey`, `Category`, `Language`, `Country`, `Channel`, `RadioStation`, `Stream`, `AnalyticsEvent`, `EpgProgramme`, `PricingTier`, `PricingFeature`, `PricingDiscount`, `Movie`, `AppSetting`.

Migrations: `backend/alembic/versions/`, currently at `018_add_app_settings_and_admin_hidden.py`. Always add a new Alembic migration for schema changes — `Base.metadata.create_all()` (used for fresh local/test DBs) must stay in sync with migration history, or endpoints that assume migration-applied types (e.g. `AnalyticsEvent.properties` as `JSONB`) will 500 on a fresh DB. See migration `017` for a past instance of this class of bug.

## Auth methods
Google OAuth (requires `email_verified`), Apple Sign-In, WebAuthn passkeys (register/login, backed by `webauthn_rp_id`/`webauthn_origin`), dev-only bypass (`POST /api/auth/dev-login`, 404s outside dev). Session = httponly cookie; mutating requests need `X-CSRF-Token` header matching the `csrf_token` cookie (double-submit, `backend/app/csrf.py`) — skipped for `Authorization: Bearer` requests, which aren't CSRF-vulnerable.

## Secrets: Vault via AppRole
`backend/app/config.py#_get_secret()` reads `adajoon:<key>` from `RevestTech/revest-vault` via AppRole (`VAULT_ADDR`/`VAULT_ROLE_ID`/`VAULT_SECRET_ID`, one-time enrollment via `revest-vault/examples/enroll.py`, never a static token), falling back to an env var of the same name if Vault has none (e.g. local dev). `backend/app/services/vault_admin_service.py`'s `MANAGED_SECRETS` lists all 12 app secrets editable from Admin → Secrets, including `jwt_secret`, `webauthn_rp_id`, `webauthn_origin`, `sentry_dsn`. `DATABASE_URL`/`REDIS_URL` are Railway service references, not vault secrets.

## Deploy topology
Railway, two services from one repo (`docker-compose.yml` mirrors this locally): backend (FastAPI, public) and frontend (React build behind nginx, internal-only, reached via the backend's proxy). A separate `worker.py` process (APScheduler) runs catalog sync jobs and records `last_sync_at` (surfaced in Admin → Overview).

## Config validation (`config.py#validate_config`)
Fails startup if: `JWT_SECRET` unset, under 32 chars, the literal `change-me-in-production`, or the built-in dev default outside `development`/`dev`; or (`ENV=production`) `DATABASE_URL`/`REDIS_URL` contain `localhost`, or Stripe is configured without a webhook secret.
