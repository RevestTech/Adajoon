import { authenticatedFetch } from "../utils/csrf";

async function parseOrThrow(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const searchAdminChannels = (q, page = 1) =>
  authenticatedFetch(
    `/api/admin/channels/search?q=${encodeURIComponent(q)}&page=${page}`
  )
    .then(parseOrThrow)
    .then((data) => data.channels);

export const setChannelHidden = (channelId, hidden) =>
  authenticatedFetch(
    `/api/admin/channels/${encodeURIComponent(channelId)}/hidden?hidden=${hidden}`,
    { method: "PATCH" }
  ).then(parseOrThrow);

export const searchAdminRadio = (q, page = 1) =>
  authenticatedFetch(`/api/admin/radio/search?q=${encodeURIComponent(q)}&page=${page}`)
    .then(parseOrThrow)
    .then((data) => data.stations);

export const setRadioHidden = (stationId, hidden) =>
  authenticatedFetch(
    `/api/admin/radio/${encodeURIComponent(stationId)}/hidden?hidden=${hidden}`,
    { method: "PATCH" }
  ).then(parseOrThrow);
