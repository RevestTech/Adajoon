const API_BASE = "/api";

export async function fetchLanguages() {
  const response = await fetch(`${API_BASE}/languages`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}
