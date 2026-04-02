import { useState, useRef, useEffect } from "react";
import UserMenu from "./UserMenu";

export default function Header({
  mode, onModeSwitch,
  search, onSearch, stats,
  sidebarOpen, onToggleSidebar,
  user, onLogin, onLogout,
}) {
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
      <button className="menu-btn" onClick={onToggleSidebar} aria-label="Toggle menu">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          {sidebarOpen
            ? <><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></>
            : <><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" /></>
          }
        </svg>
      </button>
      <div className="logo">
        Ada<span>joon</span>
      </div>

      <div className="mode-switcher">
        <button
          className={`mode-btn ${mode === "tv" ? "active" : ""}`}
          onClick={() => onModeSwitch("tv")}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="7" width="20" height="15" rx="2" ry="2" /><polyline points="17 2 12 7 7 2" />
          </svg>
          TV
        </button>
        <button
          className={`mode-btn ${mode === "radio" ? "active" : ""}`}
          onClick={() => onModeSwitch("radio")}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="2" />
            <path d="M16.24 7.76a6 6 0 0 1 0 8.49" />
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
            <path d="M7.76 16.24a6 6 0 0 1 0-8.49" />
            <path d="M4.93 19.07a10 10 0 0 1 0-14.14" />
          </svg>
          Radio
        </button>
      </div>

      <UserMenu user={user} onLogin={onLogin} onLogout={onLogout} />

      <div className="search-container">
        <svg className="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
        </svg>
        <input
          className="search-input"
          type="text"
          placeholder={mode === "tv" ? "Search TV channels, networks..." : "Search radio stations, genres..."}
          value={localSearch}
          onChange={handleChange}
        />
      </div>

      {stats && (
        <div className="header-stats">
          <span className="stat-badge">
            <strong>{stats.total_channels?.toLocaleString()}</strong> TV
          </span>
          {stats.total_radio_stations > 0 && (
            <span className="stat-badge">
              <strong>{stats.total_radio_stations?.toLocaleString()}</strong> Radio
            </span>
          )}
          <span className="stat-badge">
            <strong>{stats.total_countries}</strong> countries
          </span>
        </div>
      )}
    </header>
  );
}
