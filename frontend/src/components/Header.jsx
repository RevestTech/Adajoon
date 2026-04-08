import { useState, useRef, useEffect } from "react";
import UserMenu from "./UserMenu";

export default function Header({
  mode, onModeSwitch,
  search, onSearch,
  sidebarOpen, onToggleSidebar,
  user, onLogin, onLogout,
  showFavorites, onToggleFavorites, favoritesCount, isGuest, onGuestNotice,
  onOpenAISearch,
}) {
  const [localSearch, setLocalSearch] = useState(search);
  const debounceRef = useRef(null);
  const searchRef = useRef(null);

  useEffect(() => {
    setLocalSearch(search);
  }, [search]);

  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === "/" && !e.ctrlKey && !e.metaKey && !["INPUT", "TEXTAREA"].includes(document.activeElement?.tagName)) {
        e.preventDefault();
        searchRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, []);

  const handleChange = (e) => {
    const val = e.target.value;
    setLocalSearch(val);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => onSearch(val), 350);
  };

  return (
    <header className="header">
      <div className="header-left">
        <button className="menu-btn" onClick={onToggleSidebar} aria-label="Toggle menu">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            {sidebarOpen
              ? <><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></>
              : <><line x1="3" y1="7" x2="21" y2="7" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="17" x2="21" y2="17" /></>
            }
          </svg>
        </button>
        <div className="logo">Ada<span>joon</span></div>
      </div>

      <div className="header-center">
        <div className="mode-switcher">
          <button className={`mode-btn ${mode === "tv" ? "active" : ""}`} onClick={() => onModeSwitch("tv")}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="7" width="20" height="15" rx="2" ry="2" /><polyline points="17 2 12 7 7 2" />
            </svg>
            Television
          </button>
          <button className={`mode-btn ${mode === "radio" ? "active" : ""}`} onClick={() => onModeSwitch("radio")}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="2" />
              <path d="M16.24 7.76a6 6 0 0 1 0 8.49" />
              <path d="M7.76 16.24a6 6 0 0 1 0-8.49" />
            </svg>
            Radio
          </button>
        </div>
      </div>

      <div className="header-right">
        {isGuest ? (
          <button
            type="button"
            className="header-fav-btn header-fav-btn--guest"
            onClick={() => {
              onGuestNotice?.("Sign in to view and save favorites.");
              onLogin();
            }}
            aria-label="Favorites — sign in required"
            title="Sign in to use favorites"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
          </button>
        ) : (
          <button
            className={`header-fav-btn ${showFavorites ? "active" : ""}`}
            onClick={onToggleFavorites}
            aria-label="Favorites"
            title="Favorites"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill={showFavorites ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
            {favoritesCount > 0 && <span className="header-fav-count">{favoritesCount}</span>}
          </button>
        )}
        <div className="header-search">
          <svg className="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
          </svg>
          <input
            ref={searchRef}
            className="search-input"
            type="text"
            placeholder={mode === "tv" ? "Search channels..." : "Search stations..."}
            value={localSearch}
            onChange={handleChange}
            aria-label={mode === "tv" ? "Search channels" : "Search stations"}
          />
        </div>
        <button
          className="ai-search-btn"
          onClick={onOpenAISearch}
          aria-label="AI Search"
          title="Search with AI"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L14.09 8.26L20 9.27L15.55 13.97L16.91 20L12 16.9L7.09 20L8.45 13.97L4 9.27L9.91 8.26L12 2Z" fill="currentColor" />
          </svg>
        </button>
      </div>
      <div className="header-user">
        <UserMenu user={user} onLogin={onLogin} onLogout={onLogout} />
      </div>
    </header>
  );
}
