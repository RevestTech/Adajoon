import { authenticatedFetch } from "../utils/csrf";

const BASE = "/api/admin/movies";

async function parseOrThrow(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const fetchAdminMovies = () => authenticatedFetch(BASE).then(parseOrThrow);

export const createAdminMovie = (data) =>
  authenticatedFetch(BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }).then(parseOrThrow);

export const updateAdminMovie = (id, data) =>
  authenticatedFetch(`${BASE}/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }).then(parseOrThrow);

export const deleteAdminMovie = (id) =>
  authenticatedFetch(`${BASE}/${id}`, { method: "DELETE" }).then(parseOrThrow);
