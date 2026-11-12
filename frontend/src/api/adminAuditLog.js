import { authenticatedFetch } from "../utils/csrf";

const BASE = "/api/admin/audit-log";

async function parseOrThrow(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const fetchAuditLog = (limit = 50, offset = 0) =>
  authenticatedFetch(`${BASE}?limit=${limit}&offset=${offset}`).then(parseOrThrow);
