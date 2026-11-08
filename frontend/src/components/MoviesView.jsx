import { useEffect, useRef, useState } from "react";
import { fetchMovie, fetchMovies } from "../api/movies";
import MoviePlayer from "./MoviePlayer";

export default function MoviesView() {
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [selected, setSelected] = useState(null);
  const [opening, setOpening] = useState(false);
  const [openError, setOpenError] = useState("");
  const openRequest = useRef(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    fetchMovies()
      .then((data) => {
        if (!cancelled) setMovies(data);
      })
      .catch(() => {
        if (!cancelled) setError("Couldn't load movies. Try again later.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  // Re-fetch on open rather than reusing the cached list record, so a title
  // deactivated since the grid loaded can't still be opened from a stale card.
  const openMovie = (id) => {
    const request = ++openRequest.current;
    setOpening(true);
    setOpenError("");
    fetchMovie(id)
      .then((detail) => {
        if (request === openRequest.current) setSelected(detail);
      })
      .catch(() => {
        if (request === openRequest.current) {
          setOpenError("This movie is no longer available.");
        }
      })
      .finally(() => {
        if (request === openRequest.current) setOpening(false);
      });
  };

  if (loading) return <div className="movies-view-loading">Loading movies…</div>;
  if (error) {
    return (
      <div className="movies-view-error">
        {error}
        <button
          type="button"
          className="movies-view-retry-btn"
          onClick={() => setAttempt((n) => n + 1)}
        >
          Retry
        </button>
      </div>
    );
  }
  if (movies.length === 0) {
    return (
      <div className="movies-view-empty">
        <p>No movies yet — check back soon.</p>
      </div>
    );
  }

  return (
    <>
      {openError && <div className="movies-view-error">{openError}</div>}
      <div className="movies-grid">
        {movies.map((movie) => (
          <button
            type="button"
            key={movie.id}
            className="movie-card"
            disabled={opening}
            onClick={() => openMovie(movie.id)}
          >
            {movie.poster_url ? (
              <img src={movie.poster_url} alt={movie.title} className="movie-card-poster" />
            ) : (
              <div className="movie-card-poster movie-card-poster--placeholder" />
            )}
            <span className="movie-card-title">{movie.title}</span>
            {movie.year && <span className="movie-card-year">{movie.year}</span>}
          </button>
        ))}
      </div>
      {selected && <MoviePlayer movie={selected} onClose={() => setSelected(null)} />}
    </>
  );
}
