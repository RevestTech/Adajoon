# Status — living doc, not a roadmap

Update this when something ships or a known gap changes. If this and `PRD.md`/`TRD.md` ever disagree, trust the code and fix the docs.

## Shipped
- Core TV/radio browsing, search, EPG, map views.
- Movies vertical, syndicated catalog (#67).
- Admin dashboard as a standalone page: users, subscriptions, content moderation, pricing/ads toggle, secrets UI, ops health (#71, #55, #70).
- Self-hosted analytics: sessions, playback, auth funnel, navigation paths (`docs/CUSTOM_ANALYTICS.md`).
- Stripe billing: checkout, promo codes, webhook sync, admin comp/revoke (#66, #55).
- Parental controls: PIN set/verify/remove (current-PIN required, rate-limited), kids mode.
- Auth: Google/Apple/passkeys + dev-login bypass for local testing (#69).
- Secrets migrated from static Vault token to AppRole (per `revest-vault`'s AGENTS.md).
- Security-review pass closing CSRF/JWT-default/auth-bypass gaps (verified against code 2026-11-08: all present).
- Docs cleanup: removed 15 stale one-off incident/migration docs and scripts, added this file + `CLAUDE.md`/`PRD.md`/`TRD.md`, corrected a stale pre-Vault secrets description in `.cursor/skills/CLAUDE.md` (2026-11-08).
- Dependency sweep (2026-11-08): merged pytest 8→9 (+ fixed a `pytest-asyncio` version-ceiling break), fastapi 0.115→0.135, happy-dom bump, vite 6→8 + `@vitejs/plugin-react` 4→6 (landed together — plugin-react 6 needs vite 8's Oxc transform since it dropped Babel). Closed `#27` (Radio Garden/EPG) as superseded — the feature, and conflictingly-numbered Alembic migration `011`, already shipped on `main` independently.

## Known tech debt / explicitly deferred
- **Backend CI has likely never actually validated tests.** `tests/conftest.py`'s `TEST_DATABASE_URL` derivation (naive string-replace on `DATABASE_URL`) is buggy — confirmed two different ways by two separate agents during the 2026-11-08 sweep — and the CI test step swallows its own exit code (`|| echo "Tests not yet implemented"`), so green has not meant tests passed. Needs a real fix, not yet filed as a PR.
- **Frontend Docker image build is broken on every push to `main`**, independent of the 2026-11-08 sweep: `frontend/Dockerfile`'s `COPY frontend/...` paths assume a repo-root build context, but `ci.yml`'s `docker/build-push-action` step sets `context: ./frontend`, so every `COPY` 404s. Open, unfixed.
- Backend pins both `psycopg2-binary` and `asyncpg` — two separate Postgres drivers; redundancy worth investigating (found while validating PR #9).
- No PR merged in this session had a true GitHub-enforced approval — the session's single GitHub identity can't self-approve its own PRs, so merges went through on CI/diff checks via direct API, not a review gate. Consider branch protection if a harder gate is wanted.
- Feature-gating enforcement is a no-op — tiers don't actually restrict anything but ad-removal.
- No ad impression/fill-rate analytics.
- `whitelabel.py` router is dead code (unwired, pending a `Tenant` model) — decide keep-for-later vs delete.
- No incident/error visibility, jobs-queue UI, or audit logging (deliberate, per team size — revisit if team/scale grows).
- `react-router-dom` is a dependency but barely used — the app relies on manual `pushState` routing elsewhere; worth a decision either way rather than two routing approaches coexisting indefinitely.

## Open items
| PR | What | Status |
|---|---|---|
| #9 | python 3.12→3.14-slim (Docker base) | Open — sandbox couldn't reach `deb.debian.org` to actually build+test the image, so left unmerged. `psycopg2-binary`/`asyncpg` have no `cp314` wheels yet (would need a from-source compile); other pins (bcrypt, cryptography, pydantic, sqlalchemy) do. Needs validation outside this sandbox. |
| #28 | Adajoon ECC agent-tooling bundle | Open — not app code; its own checklist calls for human review first. |

38+ stale branches (old merged `claude/*` feature branches, plus today's merged dependabot branches that didn't auto-delete) remain on GitHub — this session's git/GitHub access blocks branch deletion (confirmed two ways: local `git push --delete` gets HTTP 403 from the sandbox proxy; no available GitHub tool exposes ref deletion). Needs cleanup via GitHub's UI directly.

Next: the 10-agent maintainability + scalability review (backend data/query layer, frontend state/bundle, auth/security, concurrency/scaling for thousands of simultaneous users, dead code, API/doc consistency, test coverage, over-engineering audit) is running as of this doc's update.
