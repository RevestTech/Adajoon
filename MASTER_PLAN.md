# Status — living doc, not a roadmap

Update this when something ships or a known gap changes. If this and `PRD.md`/`TRD.md` ever disagree, trust the code and fix the docs.

## Shipped
- Core TV/radio browsing, search, EPG, map views.
- Movies vertical, syndicated catalog (#67).
- Admin dashboard as a standalone page: users, subscriptions, content moderation, pricing/ads toggle, secrets UI, ops health (#71, #55, #70), split by domain into `admin.py`/`admin_users.py`/`admin_content.py`/`admin_analytics.py` (#80).
- Self-hosted analytics: sessions, playback, auth funnel, navigation paths (`docs/CUSTOM_ANALYTICS.md`).
- Stripe billing: checkout, promo codes, webhook sync, admin comp/revoke (#66, #55); checkout/portal endpoints rate-limited (#76).
- Parental controls: PIN set/verify/remove (current-PIN required, rate-limited), kids mode.
- Auth: Google/Apple/passkeys + dev-login bypass for local testing (#69).
- Secrets migrated from static Vault token to AppRole (per `revest-vault`'s AGENTS.md); 12 managed secrets including optional `sentry_dsn`.
- Security-review pass closing CSRF/JWT-default/auth-bypass gaps (verified against code 2026-11-08: all present).
- Docs cleanup: removed 15 stale one-off incident/migration docs and scripts, added `CLAUDE.md`/`PRD.md`/`TRD.md`/this file.
- Dependency sweep (2026-11-08): pytest 8→9, fastapi 0.115→0.135, happy-dom bump, vite 6→8 + `@vitejs/plugin-react` 4→6 (landed together). Closed `#27` (Radio Garden/EPG) as superseded.
- 10-agent maintainability/scalability review (2026-11-08), all findings fixed and merged: rate limiters consolidated onto one Redis-backed instance (#76, was silently broken under >1 backend instance), DB pool sized for real concurrency (#76), `ChannelGrid` re-render bug fixed (#81), `App.jsx`'s duplicated TV/radio state consolidated into `useCatalogList` (#79), dead code deleted — `whitelabel.py`, `psycopg2-binary`, `react-router-dom`, 12 unreferenced frontend files (#77).
- Backend CI fixed for real (#74): `conftest.py`'s broken `TEST_DATABASE_URL` derivation and the test step's swallowed exit code both fixed; surfaced and fixed 8 real pre-existing test failures (suite now 70/70 passing, not silently green).
- Frontend Docker image build fixed (#75) — was 404ing on every push to `main` (build-context mismatch), unrelated to the sweep.
- Version synced to 2.7.1 across backend/frontend (previously drifted: 2.4.0 vs 2.7.0) (#83).
- **Production incident (2026-11-09, resolved):** site was unreachable — `www.adajoon.com`/`adajoon.com` were bound to the **backend** service instead of **frontend** in Railway (visitors got the API's bare JSON instead of the site). Moved both custom domains to frontend. Root cause/timing unconfirmed (no Railway audit-log access from this session); not caused by any code change here.
- **Production incident (2026-11-08, resolved):** `start.sh` never ran migrations, so prod's schema was stuck behind the committed Alembic chain (`/api/categories` and the worker's validator both 500ing on a missing `admin_hidden` column). Fixed: `alembic upgrade head` now runs on every boot.
- Error tracking added (Sentry, optional — inert without a DSN): backend (`main.py`) and frontend (`src/sentry.js`, wired into `ErrorBoundary`). No DSN configured yet — see Open items.

## Known tech debt / explicitly deferred
- **No uptime/reachability monitoring.** Nothing watches whether the public site actually responds — the 2026-11-09 domain incident was only caught because the user noticed manually. Needs an uptime check (e.g. UptimeRobot, Better Stack) hitting `adajoon.com` with alerts to a real destination. Not something this session can set up unilaterally (third-party account signup).
- Sentry is wired but has no DSN set — error tracking is currently a no-op until one is configured (Admin → Secrets → Sentry DSN, or `SENTRY_DSN`/`VITE_SENTRY_DSN`).
- No PR merged in this session had a true GitHub-enforced approval — the session's single GitHub identity can't self-approve its own PRs, so merges went through on CI/diff checks via direct API, not a review gate. Consider branch protection if a harder gate is wanted.
- Feature-gating enforcement is a no-op — tiers don't actually restrict anything but ad-removal. Real monetization gap, not just a dev one.
- No ad impression/fill-rate analytics.
- No audit logging, jobs-queue UI, or staging environment (deliberate, per team size — revisit if team/scale grows; the two 2026-11-08/09 incidents are evidence staging + monitoring may now be worth the cost).

## Open items
| PR | What | Status |
|---|---|---|
| #9 | python 3.12→3.14-slim (Docker base) | Open — sandbox couldn't reach `deb.debian.org` to actually build+test the image, so left unmerged. `psycopg2-binary`'s removal (#77) clears one blocker; `asyncpg` still has no `cp314` wheel. Needs validation outside this sandbox. |
| #28 | Adajoon ECC agent-tooling bundle | Open — not app code; its own checklist calls for human review first. |

38+ stale branches (old merged `claude/*` feature branches, plus merged dependabot branches that didn't auto-delete) remain on GitHub — this session's git/GitHub access blocks branch deletion (confirmed: local `git push --delete` gets HTTP 403 from the sandbox proxy; no available GitHub tool exposes ref deletion). Needs cleanup via GitHub's UI directly — last known status: not yet done.
