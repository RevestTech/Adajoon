import { authenticatedFetch } from "../utils/csrf";

const BASE = "/api/admin/pricing";

async function parseOrThrow(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const fetchAdminPricingSettings = () =>
  authenticatedFetch(`${BASE}/settings`).then(parseOrThrow);

export const updateAdminPricingSettings = (data) =>
  authenticatedFetch(`${BASE}/settings`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }).then(parseOrThrow);

export const fetchAdminTiers = () => authenticatedFetch(`${BASE}/tiers`).then(parseOrThrow);

export const createAdminTier = (data) =>
  authenticatedFetch(`${BASE}/tiers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }).then(parseOrThrow);

export const updateAdminTier = (id, data) =>
  authenticatedFetch(`${BASE}/tiers/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }).then(parseOrThrow);

export const deleteAdminTier = (id) =>
  authenticatedFetch(`${BASE}/tiers/${id}`, { method: "DELETE" }).then(parseOrThrow);

export const fetchAdminFeatures = (tierId) =>
  authenticatedFetch(`${BASE}/features${tierId != null ? `?tier_id=${tierId}` : ""}`).then(
    parseOrThrow
  );

export const createAdminFeature = (data) =>
  authenticatedFetch(`${BASE}/features`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }).then(parseOrThrow);

export const updateAdminFeature = (id, data) =>
  authenticatedFetch(`${BASE}/features/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }).then(parseOrThrow);

export const deleteAdminFeature = (id) =>
  authenticatedFetch(`${BASE}/features/${id}`, { method: "DELETE" }).then(parseOrThrow);

export const fetchAdminDiscounts = () =>
  authenticatedFetch(`${BASE}/discounts`).then(parseOrThrow);

export const createAdminDiscount = (data) =>
  authenticatedFetch(`${BASE}/discounts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }).then(parseOrThrow);

export const updateAdminDiscount = (id, data) =>
  authenticatedFetch(`${BASE}/discounts/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }).then(parseOrThrow);

export const deleteAdminDiscount = (id) =>
  authenticatedFetch(`${BASE}/discounts/${id}`, { method: "DELETE" }).then(parseOrThrow);
