const BASE = "/api/radio";

export async function fetchRadioStations({ query, tag, country, language, status, page = 1, perPage = 40 }) {
  const params = new URLSearchParams();
  if (query) params.set("query", query);
  if (tag) params.set("tag", tag);
  if (country) params.set("country", country);
  if (language) params.set("language", language);
  if (status) params.set("status", status);
  params.set("page", page);
  params.set("per_page", perPage);

  const res = await fetch(`${BASE}/stations?${params}`);
  if (!res.ok) throw new Error("Failed to fetch radio stations");
  return res.json();
}

// Fallback tags if API fails
const FALLBACK_TAGS = [
  { name: "music", station_count: 5000 },
  { name: "pop", station_count: 3500 },
  { name: "news", station_count: 2800 },
  { name: "rock", station_count: 2500 },
  { name: "talk", station_count: 2200 },
  { name: "jazz", station_count: 1800 },
  { name: "classical", station_count: 1500 },
  { name: "electronic", station_count: 1400 },
  { name: "dance", station_count: 1300 },
  { name: "country", station_count: 1200 },
  { name: "hip hop", station_count: 1100 },
  { name: "sports", station_count: 1000 },
  { name: "oldies", station_count: 950 },
  { name: "80s", station_count: 900 },
  { name: "90s", station_count: 850 },
  { name: "christian", station_count: 800 },
  { name: "alternative", station_count: 750 },
  { name: "latin", station_count: 700 },
  { name: "blues", station_count: 650 },
  { name: "variety", station_count: 600 },
];

export async function fetchRadioTags() {
  try {
    const res = await fetch(`${BASE}/tags`);
    if (!res.ok) {
      // Silent fallback - no console noise
      return FALLBACK_TAGS;
    }
    return res.json();
  } catch (error) {
    // Silent fallback - no console noise
    return FALLBACK_TAGS;
  }
}

export async function fetchRadioCountries() {
  const res = await fetch(`${BASE}/countries`);
  if (!res.ok) throw new Error("Failed to fetch radio countries");
  return res.json();
}

export async function fetchRadioMap({
  bbox,
  zoom = 5,
  limit,
  workingOnly = true,
  signal,
} = {}) {
  const params = new URLSearchParams();
  params.set("bbox", bbox);
  params.set("zoom", String(zoom));
  if (limit != null) params.set("limit", String(limit));
  params.set("working_only", workingOnly ? "true" : "false");

  const res = await fetch(`${BASE}/map?${params}`, { signal });
  if (!res.ok) throw new Error("Failed to load radio map");
  return res.json();
}

export async function fetchRadioMapRide({ lat, lng, workingOnly = true, signal } = {}) {
  const params = new URLSearchParams();
  if (lat != null && Number.isFinite(Number(lat))) params.set("lat", String(lat));
  if (lng != null && Number.isFinite(Number(lng))) params.set("lng", String(lng));
  params.set("working_only", workingOnly ? "true" : "false");

  const res = await fetch(`${BASE}/map/ride?${params}`, { signal });
  if (res.status === 404) throw new Error("No station found nearby");
  if (!res.ok) throw new Error("Failed to take a ride");
  return res.json();
}
