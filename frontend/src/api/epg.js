const BASE = "/api";

/**
 * Current + next programme for a channel.
 * @param {string} channelId
 * @returns {Promise<{ channel_id: string, now: object|null, next: object|null }>}
 */
export async function fetchEpgNow(channelId) {
  const params = new URLSearchParams({ channel_id: channelId });
  const res = await fetch(`${BASE}/epg/now?${params}`);
  if (!res.ok) throw new Error("Failed to fetch EPG now/next");
  return res.json();
}

/**
 * Channels with a matching programme airing now.
 * @param {{ q?: string, category?: string, limit?: number }} opts
 */
export async function fetchEpgOnNow({ q, category, limit = 50 } = {}) {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (category) params.set("category", category);
  if (limit) params.set("limit", String(limit));
  const res = await fetch(`${BASE}/epg/now?${params}`);
  if (!res.ok) throw new Error("Failed to fetch EPG on-now");
  return res.json();
}

/**
 * Schedule window for a channel (default server window: now → +24h).
 * @param {string} channelId
 * @param {{ from?: string, to?: string }} [opts]
 */
export async function fetchChannelEpg(channelId, { from, to } = {}) {
  const params = new URLSearchParams();
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  const qs = params.toString();
  const res = await fetch(`${BASE}/channels/${encodeURIComponent(channelId)}/epg${qs ? `?${qs}` : ""}`);
  if (!res.ok) throw new Error("Failed to fetch channel EPG");
  return res.json();
}
