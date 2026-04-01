import { useState, useRef, useEffect } from "react";

export default function Header({ search, onSearch, stats }) {
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
