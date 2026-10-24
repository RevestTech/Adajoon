/** "16m left" / "1h 20m left" from a programme's stop time. */
export function formatTimeLeft(stopAt) {
  const msLeft = new Date(stopAt).getTime() - Date.now();
  if (!Number.isFinite(msLeft) || msLeft <= 0) return null;
  const totalMin = Math.round(msLeft / 60000);
  const h = Math.floor(totalMin / 60);
  const m = totalMin % 60;
  if (h > 0) return `${h}h ${m}m left`;
  return `${m}m left`;
}

/** 0-100 progress through a programme's start/stop window. */
export function epgProgressPercent(startAt, stopAt) {
  const start = new Date(startAt).getTime();
  const stop = new Date(stopAt).getTime();
  if (!Number.isFinite(start) || !Number.isFinite(stop) || stop <= start) return 0;
  const pct = ((Date.now() - start) / (stop - start)) * 100;
  return Math.min(100, Math.max(0, pct));
}

/** "2:30 PM" style absolute time for a schedule grid. */
export function formatClockTime(isoString) {
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}
