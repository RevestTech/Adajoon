import { authenticatedFetch } from "../utils/csrf";

const BASE = "/api/history";

export async function recordWatchHistory({ itemType, itemId, itemName, itemLogo = "", durationSeconds = 0 }) {
  const res = await authenticatedFetch(`${BASE}/record`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      item_type: itemType,
      item_id: itemId,
      item_name: itemName,
      item_logo: itemLogo,
      duration_seconds: durationSeconds,
    }),
  });
  if (!res.ok) throw new Error("Failed to record watch history");
  return res.json();
}

export async function fetchWatchHistory({ itemType, limit = 50 } = {}) {
  const params = new URLSearchParams();
  if (itemType) params.set("item_type", itemType);
  params.set("limit", String(limit));

  const res = await authenticatedFetch(`${BASE}/?${params}`);
  if (!res.ok) throw new Error("Failed to load watch history");
  return res.json();
}

export async function clearWatchHistory({ itemType } = {}) {
  const params = new URLSearchParams();
  if (itemType) params.set("item_type", itemType);

  const res = await authenticatedFetch(`${BASE}/?${params}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to clear watch history");
  return res.json();
}

export async function deleteWatchHistoryItem(historyId) {
  const res = await authenticatedFetch(`${BASE}/${historyId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete history item");
  return res.json();
}
