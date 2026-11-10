import { authenticatedFetch } from "../utils/csrf";

const BASE = "/api/auth/devices";

export async function fetchDevices() {
  const res = await authenticatedFetch(BASE);
  if (!res.ok) throw new Error("Failed to load devices");
  return res.json();
}

export async function removeDevice(deviceId) {
  const res = await authenticatedFetch(`${BASE}/${encodeURIComponent(deviceId)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to remove device");
  return res.json();
}
