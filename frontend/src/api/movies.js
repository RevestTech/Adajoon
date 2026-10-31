const BASE = "/api";

export async function fetchMovies() {
  const res = await fetch(`${BASE}/movies`);
  if (!res.ok) throw new Error("Failed to fetch movies");
  return res.json();
}

export async function fetchMovie(id) {
  const res = await fetch(`${BASE}/movies/${id}`);
  if (!res.ok) throw new Error("Failed to fetch movie");
  return res.json();
}
