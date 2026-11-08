import { authenticatedFetch } from "../utils/csrf";

async function parseOrThrow(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  const body = await res.json();
  // make-admin/revoke-admin return {error: "..."} with HTTP 200 on failure
  // (user not found, self-demotion) instead of raising an HTTPException.
  if (body && typeof body === "object" && body.error) {
    throw new Error(body.error);
  }
  return body;
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

// Public endpoint - the real source of truth for valid tier keys, so admin
// UIs don't hardcode a tier list that drifts from what's actually priced.
export const fetchSubscriptionTiers = () =>
  fetch(`/api/subscriptions/tiers`).then(parseOrThrow);

/** One month out, as an ISO string, for a comped subscription's expiry. */
export function oneMonthFromNow() {
  const d = new Date();
  d.setMonth(d.getMonth() + 1);
  return d.toISOString();
}
