const STORAGE_PREFIX = "adajoon_radio_popout:";
const MAX_AGE_MS = 5 * 60 * 1000;

export function stashRadioPopoutStation(station) {
  if (!station?.id) return null;
  const key = `${STORAGE_PREFIX}${station.id}`;
  const payload = { station, ts: Date.now() };
  try {
    localStorage.setItem(key, JSON.stringify(payload));
  } catch {
    return null;
  }
  return key;
}

export function loadRadioPopoutStation(stationId) {
  if (!stationId) return null;
  const key = `${STORAGE_PREFIX}${stationId}`;
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed?.station || Date.now() - (parsed.ts || 0) > MAX_AGE_MS) {
      localStorage.removeItem(key);
      return null;
    }
    return parsed.station;
  } catch {
    return null;
  }
}

export function clearRadioPopoutStation(stationId) {
  if (!stationId) return;
  try {
    localStorage.removeItem(`${STORAGE_PREFIX}${stationId}`);
  } catch {
    /* ignore */
  }
}

export function openRadioPopoutWindow(station) {
  if (!station?.id) return null;
  stashRadioPopoutStation(station);
  const url = `/?radio_popout=1&sid=${encodeURIComponent(station.id)}`;
  const features = [
    "popup=yes",
    "width=400",
    "height=640",
    "left=120",
    "top=80",
    "menubar=no",
    "toolbar=no",
    "location=no",
    "status=no",
    "resizable=yes",
    "scrollbars=no",
  ].join(",");
  return window.open(url, `adajoon-radio-${station.id}`, features);
}
