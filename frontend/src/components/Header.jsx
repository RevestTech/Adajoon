import { useState, useRef, useEffect } from "react";

export default function Header({ search, onSearch, stats, favoritesCount, showFavorites, onToggleFavorites, liveOnly, onToggleLiveOnly }) {
  const [localSearch, setLocalSearch] = useState(search);
  const debounceRef = useRef(null);

  useEffect(() => {
    setLocalSearch(search);
  }, [search]);

  const handleChange = (e) => {
    const val = e.target.value;
    setLocalSearch(val);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => onSearch(val), 350);
  };

  return (
    <header className="header">
      <div className="logo">
        Re<span>TV</span>
      </div>
      <div className="search-container">
        <svg className="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" />
        </svg>
        <input
          className="search-input"
          type="text"
          placeholder="Search channels, networks, stations..."
          value={localSearch}
          onChange={handleChange}
        />
      </div>
      <button
        className={`header-toggle-btn ${liveOnly ? "active" : ""}`}
        onClick={onToggleLiveOnly}
        title={liveOnly ? "Showing live channels only" : "Show all channels"}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="2" />
          <path d="M16.24 7.76a6 6 0 0 1 0 8.49" />
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
          <path d="M7.76 16.24a6 6 0 0 1 0-8.49" />
          <path d="M4.93 19.07a10 10 0 0 1 0-14.14" />
        </svg>
        <span className="header-toggle-label">{liveOnly ? "Live" : "All"}</span>
      </button>
      <button
        className={`header-toggle-btn ${showFavorites ? "active" : ""}`}
        onClick={onToggleFavorites}
        title="Favorites"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill={showFavorites ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
        </svg>
        {favoritesCount > 0 && <span className="header-favorites-count">{favoritesCount}</span>}
      </button>
      {stats && (
        <div className="header-stats">
          <span className="stat-badge">
            <strong>{stats.total_channels?.toLocaleString()}</strong> channels
          </span>
          <span className="stat-badge">
            <strong>{stats.total_streams?.toLocaleString()}</strong> streams
          </span>
          <span className="stat-badge">
            <strong>{stats.total_countries}</strong> countries
          </span>
        </div>
      )}
    </header>
  );
}
