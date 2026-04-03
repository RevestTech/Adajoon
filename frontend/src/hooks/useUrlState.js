const PLAYER_KEY = "adajoonPlayer";

function splitList(value) {
  if (!value || typeof value !== "string") return [];
  return value.split(",").map((s) => s.trim()).filter(Boolean);
}

/**
 * Read and decode listing-related params from the current location.
 * Also reads channel/station from URL path for shareable links.
 * @returns {{
 *   mode: 'tv'|'radio',
 *   q: string,
 *   cat: string[],
 *   country: string[],
 *   tag: string[],
 *   status: string[],
 *   page: number,
 *   view: string,
 *   fav: boolean,
 *   channel: string|null,
 *   station: string|null
 * }}
 */
export function readUrlParams() {
  const sp = new URLSearchParams(
    typeof window !== "undefined" ? window.location.search : "",
  );
  
  // Read from URL path (e.g., /tv/channel/123 or /radio/station/456)
  let channel = sp.get("channel") || null;
  let station = sp.get("station") || null;
  let modeFromPath = sp.get("mode") || "tv";
  
  if (typeof window !== "undefined") {
    const path = window.location.pathname;
    const tvMatch = path.match(/^\/tv\/channel\/([^/]+)/);
    const radioMatch = path.match(/^\/radio\/station\/([^/]+)/);
    
    if (tvMatch) {
      channel = tvMatch[1];
      modeFromPath = "tv";
    } else if (radioMatch) {
      station = radioMatch[1];
      modeFromPath = "radio";
    }
  }
  
  const modeRaw = (modeFromPath || "tv").toLowerCase();
  const mode = modeRaw === "radio" ? "radio" : "tv";
  const pageRaw = parseInt(sp.get("page") || "1", 10);
  const page = Number.isFinite(pageRaw) && pageRaw >= 1 ? pageRaw : 1;
  const viewRaw = (sp.get("view") || "").toLowerCase();
  const view = ["grid", "list", "thumb"].includes(viewRaw) ? viewRaw : "";
  const fav = sp.get("fav") === "1" || sp.get("fav") === "true";

  return {
    mode,
    q: sp.get("q") || "",
    cat: splitList(sp.get("cat") || ""),
    country: splitList(sp.get("country") || ""),
    tag: splitList(sp.get("tag") || ""),
    status: splitList(sp.get("status") || ""),
    page,
    view,
    fav,
    channel,
    station,
  };
}

/**
 * Replace the current history entry URL (listing params). Preserves existing
 * history.state (e.g. modal marker) when present.
 */
export function writeUrlParams(params) {
  if (typeof window === "undefined") return;
  const {
    mode,
    q,
    cat,
    country,
    tag,
    status,
    page,
    view,
    fav,
  } = params;

  const sp = new URLSearchParams();
  if (mode && mode !== "tv") sp.set("mode", mode);
  if (q) sp.set("q", q);
  if (cat?.length) sp.set("cat", cat.join(","));
  if (country?.length) sp.set("country", country.join(","));
  if (tag?.length) sp.set("tag", tag.join(","));
  if (status?.length) sp.set("status", status.join(","));
  if (page != null && page > 1) sp.set("page", String(page));
  if (view && view !== "grid") sp.set("view", view);
  if (fav) sp.set("fav", "1");

  const url = new URL(window.location.href);
  url.search = sp.toString();
  const next = `${url.pathname}${url.search}${url.hash}`;
  const prev =
    typeof history.state === "object" && history.state !== null
      ? history.state
      : {};
  history.replaceState(prev, "", next);
}

/**
 * Push a history entry with real URL path for shareable links.
 * @param {'tv'|'radio'} type
 * @param {string|number} id
 */
export function pushPlayerState(type, id) {
  if (typeof window === "undefined") return;
  
  // Build shareable URL path
  const path = type === "tv" ? `/tv/channel/${id}` : `/radio/station/${id}`;
  
  // Preserve query params
  const sp = new URLSearchParams(window.location.search);
  const search = sp.toString() ? `?${sp.toString()}` : "";
  
  const newUrl = `${path}${search}`;
  
  history.pushState(
    { [PLAYER_KEY]: { type, id: String(id) } },
    "",
    newUrl,
  );
}

/** 
 * Pop the player history entry (browser Back).
 * Returns to listing view with preserved filters.
 */
export function popPlayerState() {
  if (typeof window === "undefined") return;
  
  // If we're on a player URL, navigate back to root with preserved query params
  const path = window.location.pathname;
  if (path.match(/^\/(tv\/channel|radio\/station)\//)) {
    const sp = new URLSearchParams(window.location.search);
    const search = sp.toString() ? `?${sp.toString()}` : "";
    history.pushState(null, "", `/${search}`);
  } else {
    history.back();
  }
}
