import { useEffect, useRef, useState } from "react";
import {
  createAdminMovie,
  deleteAdminMovie,
  fetchAdminMovies,
  updateAdminMovie,
} from "../api/adminMovies";

const EMPTY_FORM = {
  title: "",
  stream_url: "",
  poster_url: "",
  synopsis: "",
  year: "",
  duration_minutes: "",
  genres: "",
  source: "",
};

// `Math.trunc(Number(...))` instead of `parseInt` so a `type="number"` value
// in exponent notation (e.g. "2e3") is read as its real value, not truncated
// at the "e".
const toInteger = (value) => (value ? Math.trunc(Number(value)) : null);

function toPayload(form) {
  return {
    title: form.title.trim(),
    stream_url: form.stream_url.trim(),
    poster_url: form.poster_url.trim(),
    synopsis: form.synopsis.trim(),
    genres: form.genres.trim(),
    source: form.source.trim(),
    year: toInteger(form.year),
    duration_minutes: toInteger(form.duration_minutes),
  };
}

export default function MovieManager() {
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const latestRequest = useRef(0);

  const load = () => {
    const requestId = ++latestRequest.current;
    setLoading(true);
    fetchAdminMovies()
      .then((data) => {
        if (requestId === latestRequest.current) setMovies(data);
      })
      .catch((err) => {
        if (requestId === latestRequest.current) setError(err.message);
      })
      .finally(() => {
        if (requestId === latestRequest.current) setLoading(false);
      });
  };

  useEffect(load, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.title.trim() || !form.stream_url.trim()) return;
    setSubmitting(true);
    setError("");
    try {
      await createAdminMovie(toPayload(form));
      setForm(EMPTY_FORM);
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleActive = async (movie) => {
    try {
      await updateAdminMovie(movie.id, { is_active: !movie.is_active });
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (movie) => {
    if (!window.confirm(`Remove "${movie.title}"?`)) return;
    try {
      await deleteAdminMovie(movie.id);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="pricing-manager">
      <div className="pricing-section-header">
        <h3>Movies</h3>
        <p className="settings-section-hint">
          Syndicated titles - Adajoon doesn't host video. Each entry's stream URL
          points at a syndication partner's (or other licensed source's)
          already-hosted, already-playable stream, the same model as a TV channel.
        </p>
      </div>

      {error && <p className="pricing-save-status pricing-save-status--error">{error}</p>}

      <form className="pricing-add-feature-row" onSubmit={handleSubmit}>
        <input
          className="pricing-input"
          placeholder="Title"
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          required
        />
        <input
          className="pricing-input"
          placeholder="Stream URL (from your syndication partner)"
          value={form.stream_url}
          onChange={(e) => setForm({ ...form, stream_url: e.target.value })}
          required
        />
        <input
          className="pricing-input"
          placeholder="Poster URL"
          value={form.poster_url}
          onChange={(e) => setForm({ ...form, poster_url: e.target.value })}
        />
        <input
          className="pricing-input"
          placeholder="Year"
          type="number"
          value={form.year}
          onChange={(e) => setForm({ ...form, year: e.target.value })}
        />
        <input
          className="pricing-input"
          placeholder="Duration (minutes)"
          type="number"
          value={form.duration_minutes}
          onChange={(e) => setForm({ ...form, duration_minutes: e.target.value })}
        />
        <input
          className="pricing-input"
          placeholder="Genres (comma-separated)"
          value={form.genres}
          onChange={(e) => setForm({ ...form, genres: e.target.value })}
        />
        <input
          className="pricing-input"
          placeholder="Source / partner name"
          value={form.source}
          onChange={(e) => setForm({ ...form, source: e.target.value })}
        />
        <textarea
          className="pricing-input"
          placeholder="Synopsis"
          value={form.synopsis}
          onChange={(e) => setForm({ ...form, synopsis: e.target.value })}
        />
        <button type="submit" disabled={submitting}>
          {submitting ? "Adding…" : "Add Movie"}
        </button>
      </form>

      {loading ? (
        <p>Loading…</p>
      ) : (
        <div className="admin-table">
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Year</th>
                <th>Source</th>
                <th>Active</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {movies.map((movie) => (
                <tr key={movie.id}>
                  <td>{movie.title}</td>
                  <td>{movie.year || "—"}</td>
                  <td>{movie.source || "—"}</td>
                  <td>
                    <button
                      type="button"
                      className="admin-table-action-btn"
                      onClick={() => handleToggleActive(movie)}
                    >
                      {movie.is_active ? "Active" : "Hidden"}
                    </button>
                  </td>
                  <td>
                    <button
                      type="button"
                      className="admin-table-action-btn admin-table-action-danger"
                      onClick={() => handleDelete(movie)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {movies.length === 0 && (
                <tr>
                  <td colSpan={5}>No movies yet - add one above.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
