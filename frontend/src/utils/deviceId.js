const DEVICE_ID_KEY = 'adajoon_device_id';

/**
 * Stable per-browser id sent with login requests so the backend can
 * enforce pro/family tiers' advertised device limits. Persisted in
 * localStorage, not tied to the user - it identifies this browser across
 * logins/logouts, the same thing a "devices" list means on most streaming
 * services.
 */
export function getDeviceId() {
  try {
    let id = localStorage.getItem(DEVICE_ID_KEY);
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem(DEVICE_ID_KEY, id);
    }
    return id;
  } catch {
    // Storage unavailable (private mode, blocked, etc.) - login still
    // works, it just won't count against the device limit.
    return null;
  }
}
