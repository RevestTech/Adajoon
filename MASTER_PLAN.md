# Status — living doc, not a roadmap

Update this when something ships or a known gap changes. Keep entries short — what broke/shipped, why, and the fix; skip the forensic play-by-play once it's resolved. If this and `PRD.md`/`TRD.md` ever disagree, trust the code and fix the docs.

## Shipped
- Core TV/radio browsing, search, EPG, map views. Movies vertical, syndicated catalog (#67).
- Admin dashboard: users, subscriptions, content moderation, pricing/ads toggle, secrets UI, ops health, audit log, per-phase sync status, ad fill-rate analytics — split by domain into `admin.py`/`admin_users.py`/`admin_content.py`/`admin_analytics.py` (#80).
- Self-hosted analytics: sessions, playback, auth funnel, navigation paths (`docs/CUSTOM_ANALYTICS.md`).
- Stripe billing: checkout, promo codes, webhook sync, admin comp/revoke, rate-limited checkout/portal endpoints. Device-limit enforcement for Pro/Family tiers, with self-service device management under Settings.
- Parental controls: PIN set/verify/remove (rate-limited), Kids Mode actually filters content server-side (fixed 2026-11-15, was cosmetic-only before).
- Auth: Google/Apple/passkeys + dev-login bypass for local testing. Apple Sign-In's "Completing sign-in..." hang fixed (2026-11-23, CSP had no allowance for its relay script).
- Secrets on Vault AppRole (12 managed secrets, optional `sentry_dsn`). Error tracking wired (Sentry, backend+frontend) but inert — no DSN configured yet.
- CI is a real gate: backend tests, frontend ESLint/tests all actually block merge now (previously several were piped to `|| true` — see audit below). `mypy`/Prettier run and report but aren't hard gates yet (large pre-existing baseline on both).
- iOS PWA install instructions (2026-11-23): `InstallPrompt.jsx` only ever listened for `beforeinstallprompt`, which iOS Safari never fires — the component rendered nothing for any iOS visitor. Added UA-based iOS/iPadOS detection that shows manual "Tap Share → Add to Home Screen" instructions instead.
- Mobile UX pass (2026-11-14 through 2026-11-23): persistent bottom tab bar, filters as a bottom sheet, search by country/name, landing-page scroll trap / unstyled modals / cramped filter bar / EPG now-line drift fixed. Full detail below.
- Version synced 2.4.0→2.7.1→2.8.1→2.9.0 across backend/frontend (was drifted once, #83).

### Recent incidents (all resolved same-day)
Recurring lesson across three of these: **CI green doesn't prove the real deploy artifact builds** — it only proves *a* build succeeded under CI's toolchain, which has repeatedly differed from Railway's. Validate the actual Railway build/deploy after merging anything touching Dockerfiles or lockfiles, don't trust CI alone.
- **2026-11-09** — prod domains were bound to the backend service instead of frontend (visitors got raw JSON). Moved both custom domains to frontend.
- **2026-11-08** — prod DB was stuck behind the committed Alembic chain (`start.sh` never ran migrations). Fixed: `alembic upgrade head` now runs on every boot.
- **2026-11-23** — `python:3.15-slim` bump (dependabot #99) broke the real Docker build (no `pydantic-core` wheel for CPython 3.15, source compile fails in the slim image). CI's Docker-build job only runs on push to `main`, not on PRs, so this wasn't caught pre-merge. Reverted to `3.12-slim`. **Tech debt:** that CI gap is still open, see below.
- **2026-11-23** — `maplibre-gl` v5→v6 bump (dependabot #130, fixes a critical XSS advisory GHSA-jrc7-96c5-q579) needed two real code fixes to actually ship: a namespace import (v6 dropped the default export) and explicit Worker URL registration via `?worker&url` (v6's `import.meta.url`-based worker resolution doesn't survive Vite's hashed prod bundling — production-build-only bug, `npm run dev` never shows it).
- **2026-11-23** — the above fix's locally-regenerated lockfile (made with npm 10.9.9 + `--legacy-peer-deps`) was missing platform-specific optional-dependency entries, so it passed GitHub Actions' `npm ci` but failed Railway's (npm 11.x, stricter). Fixed by regenerating with npm 11.20.0 to match Railway's build image. Site was never actually down — Railway doesn't cut over to a failed build.
- **2026-11-23** — after that deploy, `/api/*` saw intermittent 502/504s for several minutes (stale nginx→backend proxy connection from the whole-project redeploy). Resolved by restarting backend then frontend.

## Known tech debt / explicitly deferred
- **"Build Docker Images" CI job never runs on pull requests, only on push to `main`.** Should run (build-only, no push) on any PR touching `backend/Dockerfile`, `backend/requirements.txt`, or `frontend/package*.json` — this exact gap caused two production incidents above.
- **No uptime/reachability monitoring** — nothing alerts if the public site stops responding. Needs a third-party uptime check (UptimeRobot, Better Stack); not something this session can set up unilaterally (account signup required).
- Sentry has no DSN set — inert until configured (Admin → Secrets, or `SENTRY_DSN`/`VITE_SENTRY_DSN`).
- No PR merged in this session had a true GitHub-enforced approval (single identity can't self-approve). Consider branch protection if a harder gate is wanted.
- Feature-gating is a no-op beyond ads — 4K quality and offline downloads are advertised Pro/Family features but nothing checks for them. Real monetization gap.
- No audit-log tamper-evidence (no hash chain / write protection) and no staging environment — deliberate for team size, revisit if it grows.
- Vault secret rotation can silently no-op if a same-named env var is still set on the Railway service — it wins over the vault value with no error.
- 38+ stale branches (merged `claude/*`/dependabot branches that didn't auto-delete) remain on GitHub — this session's git access can't delete refs (`git push --delete` gets HTTP 403 from the sandbox proxy, no GitHub tool exposes ref deletion). Needs cleanup via GitHub's UI.

## Codebase audit — 2026-11-15
60-subagent review (20 dimensions × wiring/best-practice/security), adversarially re-verified. 108 confirmed findings (30 wiring, 52 best-practice, 26 security). Full list: `docs/AUDIT_2026-11-15.md` (point-in-time snapshot, not updated per-finding — status below is current).

Top criticals: Kids Mode no-op, rate limiting never registered, AI search auth/rate-limit + radio UUID bug, and CI lint/test no-op gates — **all fixed** (same week this audit ran). Still open: Vault secret rotation silent no-op, admin audit-log tamper-evidence, 4K/offline-downloads feature-gating (all three listed under tech debt above).

## Open items
| PR | What | Status |
|---|---|---|
| #105 | `@vitest/ui` 5.1.0→5.1.1 (dependabot) | Open — routine follow-up patch now that the matching `vitest` peer bump (#137) landed; should be safe to merge as-is. |

## Mobile UX
10-agent review (2026-11-14) across header/nav, filters, grid/list, player modals, touch targets, typography, map/EPG, loading states — plus later user-reported real-phone screenshots.

**Fixed:** landing-page scroll trap; unstyled Settings/Pricing modals; filter bar wrap bug; EPG now-line drift; header-search breakpoint conflict (32px/12px font regression); header icon buttons <44px; list-view fixed-width columns squeezing channel names; `.channel-card` missing `min-width:0` causing radio-card overflow; duplicate React keys in `WorldMap.jsx` (Cyprus/Somalia shared ids); Radio Garden Map's "Take a ride" button overlapping the attribution strip; sidebar-collapse CSS specificity bug leaving a blank gap at 769–1024px; mobile filter-sheet chip font size mismatch; bottom tab bar now hides-on-scroll-down to avoid stacking with the browser's own toolbar.

**Still open (by priority):**
- High: more touch targets under 44px (player modal header buttons, favorite-btn gap, map zoom buttons, radio map pins, pagination, AI-search button); header's 3 overlapping mobile media-query breakpoints need full consolidation (only the actively-regressing pair was removed); `.back-to-top`/`.install-prompt` don't consistently handle the mini-player or safe-area-inset; skeleton loaders don't match real card sizing; `.stream-switcher` has no wrap for 3+ streams; long channel-modal titles have no ellipsis handling.
- Medium: a few text elements still drop to 8-9px on mobile (`.channel-tag`, `.filter-group-label`, `.recent-item-name`); EPG names cramped at mobile column width; redundant filter-group labels eat horizontal space.

**Design exploration (not implemented):** a standalone interactive prototype explored a bottom tab bar, full-screen search, swipe-to-change-channel, filters-as-sheet, and pull-to-refresh, synthesized from 20 parallel expert-opinion agents plus review against reference apps (Apple Music Radio, myTuner). Bottom tab bar, filter sheet, and country-search already shipped for real (above). Still just prototyped: full-screen search overlay, player swipe gestures, pull-to-refresh, long-press card actions, first-run country/genre picker, a distinct "Continue watching" row, pure-black player background, grouped settings sections — each needs its own scoped PR.
