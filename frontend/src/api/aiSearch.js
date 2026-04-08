const BASE = "/api";

/**
 * AI-powered natural language search.
 * @param {string} query - Natural language query
 * @param {"tv"|"radio"} mode - Search mode
 * @returns {Promise<Object>} Search results with channels/stations and explanation
 */
export async function aiSearch(query, mode = "tv") {
  const res = await fetch(`${BASE}/search/ai`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, mode }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "AI search failed");
  }
  return res.json();
}

/**
 * Check AI search availability.
 * @returns {Promise<Object>} Status object with enabled, has_api_key, model
 */
export async function getAISearchStatus() {
  const res = await fetch(`${BASE}/search/ai/status`);
  if (!res.ok) throw new Error("Failed to check AI search status");
  return res.json();
}
