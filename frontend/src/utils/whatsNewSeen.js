const LAST_SEEN_KEY = "adajoon_whats_new_seen_version";

export function hasUnseenWhatsNew(latestVersion) {
  if (!latestVersion) return false;
  try {
    return localStorage.getItem(LAST_SEEN_KEY) !== latestVersion;
  } catch {
    return false;
  }
}

export function markWhatsNewSeen(latestVersion) {
  if (!latestVersion) return;
  try {
    localStorage.setItem(LAST_SEEN_KEY, latestVersion);
  } catch {
    /* ignore */
  }
}
