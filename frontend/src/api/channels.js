const BASE = "/api";

export async function fetchChannels({ query, category, country, language, page = 1, perPage = 40 }) {
  const params = new URLSearchParams();
  if (query) params.set("query", query);
  if (category) params.set("category", category);
  if (country) params.set("country", country);
  if (language) params.set("language", language);
  params.set("page", page);
  params.set("per_page", perPage);

  const res = await fetch(`${BASE}/channels?${params}`);
  if (!res.ok) throw new Error("Failed to fetch channels");
  return res.json();
}

export async function fetchCategories() {
  const res = await fetch(`${BASE}/categories`);
  if (!res.ok) throw new Error("Failed to fetch categories");
  return res.json();
}

export async function fetchCountries() {
  const res = await fetch(`${BASE}/countries`);
  if (!res.ok) throw new Error("Failed to fetch countries");
  return res.json();
}

export async function fetchStats() {
  const res = await fetch(`${BASE}/stats`);
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export async function fetchStreams(channelId) {
  const res = await fetch(`${BASE}/channels/${channelId}/streams`);
  if (!res.ok) throw new Error("Failed to fetch streams");
  return res.json();
}
