/**
 * Guest-mode "continue as guest" flag.
 *
 * Backed by both localStorage and a long-lived cookie. localStorage alone
 * is unreliable for this: Safari's Intelligent Tracking Prevention purges
 * script-writable storage (localStorage/IndexedDB) after ~7 days without
 * user interaction on the site, silently clearing the flag and sending
 * returning guests back through the sign-in gate. A first-party cookie
 * isn't subject to that cap, so it's used as the durable fallback.
 */

const GUEST_SKIP_KEY = "adajoon_guest_skip";
const GUEST_SKIP_MAX_AGE_DAYS = 365;

function readCookie(name) {
  const match = document.cookie.match(
    new RegExp(`(?:^|; )${name}=([^;]*)`)
  );
  return match ? decodeURIComponent(match[1]) : null;
}

function writeCookie(name, value, maxAgeDays) {
  const maxAge = maxAgeDays * 24 * 60 * 60;
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=${maxAge}; samesite=lax`;
}

function clearCookie(name) {
  document.cookie = `${name}=; path=/; max-age=0`;
}

export function hasSkippedGuestLogin() {
  try {
    if (localStorage.getItem(GUEST_SKIP_KEY)) return true;
  } catch {
    // localStorage unavailable - fall through to cookie check
  }
  try {
    return Boolean(readCookie(GUEST_SKIP_KEY));
  } catch {
    return false;
  }
}

export function setSkippedGuestLogin() {
  try {
    localStorage.setItem(GUEST_SKIP_KEY, "1");
  } catch {
    // Ignore - cookie below still covers it
  }
  try {
    writeCookie(GUEST_SKIP_KEY, "1", GUEST_SKIP_MAX_AGE_DAYS);
  } catch {
    // Ignore
  }
}

export function clearSkippedGuestLogin() {
  try {
    localStorage.removeItem(GUEST_SKIP_KEY);
  } catch {
    // Ignore
  }
  try {
    clearCookie(GUEST_SKIP_KEY);
  } catch {
    // Ignore
  }
}
