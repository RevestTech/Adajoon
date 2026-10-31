import { authenticatedFetch } from "../utils/csrf";

async function parseOrThrow(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const fetchAdminUsers = ({ q = "", tier = "", adminOnly = false, page = 1 } = {}) => {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (tier) params.set("tier", tier);
  if (adminOnly) params.set("admin_only", "true");
  params.set("page", page);
  return authenticatedFetch(`/api/admin/users?${params}`).then(parseOrThrow);
};

export const updateAdminUser = (userId, data) =>
  authenticatedFetch(`/api/admin/users/${userId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }).then(parseOrThrow);

export const makeUserAdmin = (userId) =>
  authenticatedFetch(`/api/admin/users/${userId}/make-admin`, { method: "POST" }).then(
    parseOrThrow
  );

export const revokeUserAdmin = (userId) =>
  authenticatedFetch(`/api/admin/users/${userId}/revoke-admin`, {
    method: "POST",
  }).then(parseOrThrow);

export const fetchAdminSubscriptions = () =>
  authenticatedFetch(`/api/admin/subscriptions`).then(parseOrThrow);

export const fetchAdminRevenue = () =>
  authenticatedFetch(`/api/admin/revenue`).then(parseOrThrow);
