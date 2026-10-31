const YOUTUBE_URL_RE =
  /(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;

/**
 * Extract an 11-char YouTube video id from a watch/share/embed URL, or null
 * if the URL isn't a YouTube link.
 */
export function getYoutubeVideoId(url) {
  if (!url || typeof url !== "string") return null;
  const match = url.match(YOUTUBE_URL_RE);
  return match ? match[1] : null;
}

/**
 * Extract a start-time offset in whole seconds from a YouTube URL's `t=` or
 * `start=` query param (e.g. `?t=4775s`, `?t=1h5m` or `?start=90`), or 0 if
 * the URL carries none.
 */
export function getYoutubeStartSeconds(url) {
  if (!url || typeof url !== "string") return 0;
  let parsed;
  try {
    parsed = new URL(url);
  } catch {
    return 0;
  }
  const raw = parsed.searchParams.get("t") || parsed.searchParams.get("start");
  if (!raw) return 0;

  if (/^\d+$/.test(raw)) return parseInt(raw, 10);

  const hms = raw.match(/^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$/);
  if (!hms || !(hms[1] || hms[2] || hms[3])) return 0;
  const [, h, m, s] = hms;
  return (parseInt(h || "0", 10) * 3600) + (parseInt(m || "0", 10) * 60) + parseInt(s || "0", 10);
}
