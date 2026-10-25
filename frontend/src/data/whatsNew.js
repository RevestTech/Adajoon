/**
 * Curated, user-facing release notes. Newest first.
 *
 * This is deliberately separate from CHANGELOG.md: the changelog is a full
 * technical record (every fix, every lint pass); this is a short, plain-
 * language highlight reel shown to end users and in the admin dashboard.
 * Add an entry here when a release ships something worth telling users
 * about - not for internal/invisible changes (lint cleanup, test fixes,
 * refactors).
 */
export const WHATS_NEW = [
  {
    version: "2.7.0",
    date: "2026-10-25",
    highlights: [
      "New: live current-track titles on radio station cards and the player, pulled from each station's own stream",
      "New: admin pricing manager — set tier prices, bundled or paid add-on features, and discount codes without a code change",
      "New: no-login \"For You\" row on the TV home screen, built from your own watch history",
    ],
  },
  {
    version: "2.6.2",
    date: "2026-10-24",
    highlights: [
      "Fixed: guest mode now stays signed out on reload instead of bouncing back to sign-in",
      "Fixed: channels and stations recover automatically when a stream fails, instead of freezing silently",
      "Fixed: sharing a direct link to a channel or station now opens the player right away",
      "Fixed: broken or mistyped links now show a clear \"not found\" page",
      "Fixed: the mobile header no longer overflows the screen",
    ],
  },
  {
    version: "2.6.0",
    date: "2026-07-21",
    highlights: [
      "New: Radio World Map — explore stations by location, with a \"Take a ride\" shuffle",
      "New: live TV EPG (what's on now / next) on supported channels",
      "New: pop-out floating player so you can keep browsing while watching or listening",
    ],
  },
];

/** The latest version in WHATS_NEW, used to detect unseen releases. */
export const LATEST_VERSION = WHATS_NEW[0]?.version || null;

/**
 * Formats a "YYYY-MM-DD" release date as a local calendar date without the
 * off-by-one you get from `new Date("YYYY-MM-DD")`, which parses as UTC
 * midnight and can render as the previous day in timezones west of UTC.
 */
export function formatReleaseDate(isoDate) {
  const [year, month, day] = isoDate.split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString(undefined, {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}
