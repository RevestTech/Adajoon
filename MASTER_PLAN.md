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

## Known tech debt / explicitly deferred
- Feature-gating enforcement is a no-op — tiers don't actually restrict anything but ad-removal.
- No ad impression/fill-rate analytics.
- `whitelabel.py` router is dead code (unwired, pending a `Tenant` model) — decide keep-for-later vs delete.
- No incident/error visibility, jobs-queue UI, or audit logging (deliberate, per team size — revisit if team/scale grows).
- `react-router-dom` is a dependency but barely used — the app relies on manual `pushState` routing elsewhere; worth a decision either way rather than two routing approaches coexisting indefinitely.

## Open items (dependency PRs left unmerged after 2026-11-08 review pass)
| PR | What | Why blocked |
|---|---|---|
| #7 | pytest 8→9 | `Test Backend` CI fails on this PR |
| #9 | python 3.12→3.14-slim (Docker base) | Major base-image bump, never actually exercised by CI (build step skipped) — needs a manual build/test before merging |
| #13 | fastapi 0.115→0.135 | Merge-conflicted (lockfile) after neighboring PRs merged; needs rebase |
| #14 | @vitejs/plugin-react 4→6 | Frontend test/lint fail (Babel-related) |
| #21 | vite 6→8 | Frontend test/lint fail; likely needs to land together with #14 |
| #24 | happy-dom bump | Merge-conflicted (lockfile) after neighboring PRs merged; needs rebase |
| #27 | Radio Garden map + TV EPG | Still draft, stale vs. current main |
| #28 | Adajoon ECC agent-tooling bundle | Not app code; its own checklist calls for human review first |

Next: a 10-agent maintainability + scalability review (backend data/query layer, frontend state/bundle, auth/security, concurrency/scaling for thousands of simultaneous users, dead code, API/doc consistency, test coverage, over-engineering audit) — not yet run as of this doc's creation.
