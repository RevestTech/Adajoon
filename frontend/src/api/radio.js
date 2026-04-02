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

export async function fetchRadioTags() {
  const res = await fetch(`${BASE}/tags`);
  if (!res.ok) throw new Error("Failed to fetch radio tags");
  return res.json();
}

export async function fetchRadioCountries() {
  const res = await fetch(`${BASE}/countries`);
  if (!res.ok) throw new Error("Failed to fetch radio countries");
  return res.json();
}
