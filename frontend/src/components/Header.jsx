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
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          {sidebarOpen
            ? <><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></>
            : <><line x1="3" y1="7" x2="21" y2="7" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="17" x2="21" y2="17" /></>
          }
        </svg>
      </button>

      <div className="logo">Ada<span>joon</span></div>

      <div className="mode-switcher">
        <button className={`mode-btn ${mode === "tv" ? "active" : ""}`} onClick={() => onModeSwitch("tv")}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="7" width="20" height="15" rx="2" ry="2" /><polyline points="17 2 12 7 7 2" />
          </svg>
          TV
        </button>
        <button className={`mode-btn ${mode === "radio" ? "active" : ""}`} onClick={() => onModeSwitch("radio")}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="2" />
            <path d="M16.24 7.76a6 6 0 0 1 0 8.49" />
            <path d="M7.76 16.24a6 6 0 0 1 0-8.49" />
          </svg>
          Radio
        </button>
      </div>

      <div className="header-search">
        <svg className="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
        </svg>
        <input
          className="search-input"
          type="text"
          placeholder={mode === "tv" ? "Search TV channels, networks..." : "Search stations, genres..."}
          value={localSearch}
          onChange={handleChange}
        />
      </div>

      {stats && (
        <div className="header-stats">
          <span className="stat-pill">{stats.total_channels?.toLocaleString()} <small>TV</small></span>
          {stats.total_radio_stations > 0 && (
            <span className="stat-pill">{stats.total_radio_stations?.toLocaleString()} <small>Radio</small></span>
          )}
        </div>
      )}

      <div className="header-user">
        <UserMenu user={user} onLogin={onLogin} onLogout={onLogout} />
      </div>
    </header>
  );
}
