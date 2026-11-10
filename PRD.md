# Product Requirements — current state

Adajoon (repo: ReTV) is a streaming aggregator and front-end, not a content host: it points at already-hosted, already-playable streams (TV channel feeds, radio stations, syndicated movie partners) rather than hosting/transcoding media itself.

## Core verticals
- **TV**: 39k+ live channels, search/filter by category/language/country, EPG (program guide), map view.
- **Radio**: stations with a Radio Garden-style map, search/filter.
- **Movies**: syndicated catalog (partner-hosted `stream_url`, same pattern as TV channels), admin-managed, no automated feed integration yet (titles added by hand).

## Monetization
- Free tier with ads (global on/off kill switch in Admin → Pricing, backed by `app_settings`).
- Paid tiers via Stripe (checkout, promo codes, webhook-synced subscription state).
- Admin can comp/revoke a subscription directly (support overrides); Stripe stays the source of truth for real subscriptions.

## Auth
Google OAuth, Apple Sign-In, WebAuthn passkeys, plus a dev-only login bypass (404s outside `ENV=dev|development`). Google logins require `email_verified`. Session via cookie + CSRF double-submit.

## Admin dashboard (`/admin`, real page not a modal)
- Overview: DB/Redis health, last catalog sync time.
- Users: search, make/revoke admin, clear locked parental PINs.
- Subscriptions: list + rough MRR, comp/revoke.
- Content moderation: hide/unhide channels & radio stations (`admin_hidden`, independent of the sync jobs' `is_active`).
- Movies: CRUD catalog.
- Pricing: tiers, feature add-ons, discount codes, ads toggle.
- Secrets: write vault-backed app secrets (11 keys, see `TRD.md`).

## Parental controls
Per-user PIN (bcrypt-hashed) gates "kids mode"; removing a PIN requires the current PIN; PIN verify/remove endpoints are rate-limited (10/min).

## Analytics
Self-hosted (own Postgres, no third-party service) — session/playback heartbeats, auth funnel, navigation/screen paths. Full schema and API in `docs/CUSTOM_ANALYTICS.md`.

## Explicitly out of scope / deliberately not built
(Flagged in PR #71 and still true unless a later PR says otherwise — check `MASTER_PLAN.md`'s Shipped list before assuming any of these landed.)
- Feature-gating enforcement — every advertised tier feature besides ad-removal is currently unenforced.
- Ad impression/fill-rate tracking — no analytics events exist for this yet.
- Error/incident visibility, a jobs-queue UI, audit logging — not worth it at this team's current size.
- Multi-tenant/white-label support — was a dead, unwired router pending a `Tenant` model; deleted in the 2026-11-08 cleanup sweep.
