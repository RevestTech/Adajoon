const BASE = "/api/auth";

/**
 * Top channels or stations by net community vote score, for the search
 * box's default (empty-query) trending suggestions.
 * @param {"tv"|"radio"} itemType
 * @returns {Promise<{id: string, name: string, logo: string}[]>}
 */
export async function fetchTrending(itemType) {
  const params = new URLSearchParams({ item_type: itemType });
  const res = await fetch(`${BASE}/votes/trending?${params}`);
  if (!res.ok) throw new Error("Failed to fetch trending");
  return res.json();
}
