# ReTV (Adajoon)

Streaming aggregator: 39k+ live TV channels, radio stations, and syndicated movies. Free tier (ads) + paid tiers (Stripe). React frontend, FastAPI backend, deployed on Railway.

## Where things live

| Feature | Backend | Frontend |
|---|---|---|
| Auth (Google/Apple/passkey/dev-bypass) | `backend/app/routers/auth.py` | `frontend/src/` auth components/hooks |
| CSRF | `backend/app/csrf.py`, `backend/app/routers/csrf.py` | — |
| TV channels | `backend/app/routers/channels.py`, `epg.py` | `frontend/src/components`, `hooks` |
| Radio | `backend/app/routers/radio.py` | same |
| Movies | `backend/app/routers/movies.py`, `admin_movies.py` | same |
| Subscriptions / Stripe | `backend/app/routers/subscriptions.py` | — |
| Parental controls | `backend/app/routers/parental.py` | `frontend/src/hooks/useParentalControls.js` |
| Admin dashboard | `backend/app/routers/admin*.py` | `frontend/src/components/AdminDashboard.jsx` |
| Secrets (Vault) | `backend/app/config.py`, `backend/app/vault_client.py`, `backend/app/services/vault_admin_service.py` | Admin → Secrets tab |
| Analytics (self-hosted) | `backend/app/routers/analytics.py` | `frontend/src/analytics.js` |
| Background sync | `backend/app/worker.py` | — |
| DB schema | `backend/alembic/versions/` (head: `018_add_app_settings_and_admin_hidden.py`) | — |

`whitelabel.py` router exists but is **not wired up** (`main.py`: `# app.include_router(whitelabel.router)  # TODO: Implement Tenant model first`) — dead code pending a decision, not a bug.

## Run locally

See `README.md` and `docker-compose.yml`. Run migrations with `./run-migrations.sh`.

## More context

- Full AI working-agreement & conventions (backend/frontend/security/database/deployment patterns): `.cursor/skills/CLAUDE.md`
- Product scope: `PRD.md`
- Technical architecture: `TRD.md`
- Current status / known debt / open PRs: `MASTER_PLAN.md`
- Feature-specific deep-dives: `docs/` (analytics, floating player, radio map/EPG, Railway monitoring, TV optimization, admin access)
