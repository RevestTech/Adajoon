import { useEffect, useState } from "react";
import { fetchMovies } from "../api/movies";
import MoviePlayer from "./MoviePlayer";

export default function MoviesView() {
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);

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
  }, []);

  if (loading) return <div className="movies-view-loading">Loading movies…</div>;
  if (error) return <div className="movies-view-error">{error}</div>;
  if (movies.length === 0) {
    return (
      <div className="movies-view-empty">
        <p>No movies yet — check back soon.</p>
      </div>
    );
  }

  return (
    <>
      <div className="movies-grid">
        {movies.map((movie) => (
          <button
            type="button"
            key={movie.id}
            className="movie-card"
            onClick={() => setSelected(movie)}
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
