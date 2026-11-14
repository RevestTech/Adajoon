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
| #99 | python 3.12→3.15-slim (dependabot, supersedes #9) | Open — 3-version jump, too risky to merge right after the 2026-11-14 outage without dedicated testing. |
| #105 | `@vitest/ui` 4→5 (dependabot) | Open — CI red (Lint Frontend, Test Frontend both fail). Needs `vitest` core bumped alongside it, not just the UI companion package. |

## Mobile UX — 10-agent review (2026-11-14), not yet fixed
Found via 10 parallel read-only review agents (header/nav, filter bar, grid/list, player modals, touch targets, typography, bottom-stacking, settings/pricing, landing page, map/EPG, loading states) prompted by a user-reported screenshot of oversized/empty channel cards (that specific bug is already fixed, PR #109). Nothing below has been fixed yet — tracked here so it isn't lost.

**Critical (actually broken, not just cramped):**
- Landing page (`LandingPage.jsx`/`.landing-page`) has `overflow: hidden` with no scroll fallback. On an iPhone with Safari + Apple login + passkeys (the common real-world config), estimated content height (~665px) exceeds usable viewport height after the address bar — "Continue as guest" and the Passkey button can be pushed off-screen with no way to reach them.
- `SettingsPage.jsx` and `PricingPage.jsx` use `.admin-modal-overlay`/`.admin-modal` classes that have **zero CSS rules anywhere in the codebase** — these pages render as unstyled inline HTML (no overlay/backdrop/centering/scroll-clamp, unstyled close button). Not mobile-specific, but worse there.
- Filter bar (`.quality-filter`, index.css ~2150 base rule) has `flex-wrap: wrap` from the desktop rule, never reset to `nowrap` in the mobile override (~4685) that's supposed to turn it into a horizontal-scroll row (comment there says so) — causes the cramped 2-line wrap a user screenshotted.
- EPG grid (`EpgGridView.jsx:114`) hardcodes the channel-column offset as `160px` for the "now" red line position, but CSS shrinks that column to `100px` on mobile (index.css:7789) — the current-time indicator renders 60px off from the actual time on phones.

**High (real usability problems):**
- Touch targets under 44px in ~10 places: `.modal-close` (every modal's close button, no fixed size at all), `.modal-favorite-btn`/`.modal-minimize`/`.modal-popout`/`.modal-share-btn` (player modal header, 36px), `.favorite-btn` has a gap at 481-768px widths (still 38px), header icon buttons `.pricing-nav-btn`/`.whats-new-btn`/`.theme-toggle-btn` (36px, no mobile override), collapsed `.header-search` (32px wide), `.world-map-zoom-btn`/`.world-map-zoom-reset` (shrinks the *wrong* way: 36→32→28px as screens get smaller), radio map pins `.radio-garden-map__marker` (10×10px), pagination buttons (~30-34px), `.ai-search-btn` (38px).
- iOS Safari auto-zoom bug: `.search-input` is 13-15px on mobile (index.css:4603, 4747) — any input under 16px triggers an unwanted page-zoom on focus on iOS.
- List view (`.list-row`, index.css:2425) has fixed-width columns (42+88+100+44px) that were never adjusted for mobile — on a 375px screen the channel name column gets squeezed to almost nothing.
- Header has three separate, overlapping mobile media-query blocks (`@768px`, `@480px`, `@640px`) for the same selectors, fighting each other via `!important` — actual rendered behavior is an unintended mix, not deliberate design. Needs consolidation into one block per selector.
- `.back-to-top` and the PWA `.install-prompt` don't account for the mini-player (`.mini-player`) being open, and neither adds `env(safe-area-inset-bottom)` consistently — can overlap the mini-player's playback controls or sit in the iPhone home-indicator zone.
- Skeleton loaders (`.skeleton-card`) don't share a class with `.channel-card`, so they don't match its `min-height` — real content visibly jumps in size once it loads.
- `.stream-switcher` (player modal) has no `flex-wrap` — 3+ simultaneous streams can overflow a narrow screen with no visual scroll affordance.
- Channel modal title (`.channel-modal-header h3`) has no overflow/ellipsis handling — long channel names wrap to 2 lines and crowd the row of action icons next to it.

**Medium (readability/polish):**
- Several text elements drop to 8-9px on mobile (`.channel-tag`, `.channel-stream-badge`, `.filter-group-label`, `.recent-item-name`) — below comfortable reading size.
- EPG channel names/programme titles are cramped at the mobile grid-column width (~100px) and 4-hour window — mostly truncated.
- Redundant `.filter-group-label`s (e.g. "System Status:") eat horizontal space in what should be a scrolling filter-chip row.

## Mobile UX — proposed improvements (not bugs, new interaction patterns)
Prototyped interactively — see the Adajoon mobile prototype artifact from this session. Status per item:
1. Bottom tab bar for TV/Radio/Map/Movies, replacing the cramped top-header icon row. Not started — this is a navigation-architecture change, not a drop-in fix.
2. Full-screen search overlay on tap, instead of a small inline-expanding search bar. Not started.
3. Swipe left/right in the channel/station player to jump to the next/previous item, instead of closing the modal and tapping another card. Not started.
4. **Shipped** (`MobileFilterSheet.jsx`): on real phones (≤640px), the Verified/Live Now/Has Stream/etc. filter row opens as a tap-to-open bottom sheet with a sticky "Show results" button, instead of a horizontal-scroll strip. Tablets (641-768px) keep the scroll row; desktop is unchanged (the wrapper is `display: contents` there). Applied to both `ChannelGrid.jsx` and `RadioGrid.jsx`.
5. Pull-to-refresh on the channel/station grid. Not started.

38+ stale branches (old merged `claude/*` feature branches, plus merged dependabot branches that didn't auto-delete) remain on GitHub — this session's git/GitHub access blocks branch deletion (confirmed: local `git push --delete` gets HTTP 403 from the sandbox proxy; no available GitHub tool exposes ref deletion). Needs cleanup via GitHub's UI directly — last known status: not yet done.
