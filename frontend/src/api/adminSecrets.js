import { authenticatedFetch } from "../utils/csrf";

const BASE = "/api/admin/secrets";

async function parseOrThrow(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const fetchAdminSecrets = () => authenticatedFetch(BASE).then(parseOrThrow);

export const setAdminSecret = (key, value) =>
  authenticatedFetch(`${BASE}/${encodeURIComponent(key)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value }),
  }).then(parseOrThrow);

export const clearAdminSecret = (key) =>
  authenticatedFetch(`${BASE}/${encodeURIComponent(key)}`, {
    method: "DELETE",
  }).then(parseOrThrow);
