import { useState, useRef, useEffect, useCallback } from "react";
import UserMenu from "./UserMenu";
import { fetchTrending } from "../api/trending";

export default function Header({
  mode, onModeSwitch,
  search, onSearch,
  sidebarOpen, onToggleSidebar,
  user, onLogin, onLogout,
  showFavorites, onToggleFavorites, favoritesCount, isGuest, onGuestNotice,
  onOpenAISearch,
  onOpenAdmin,
  onOpenWhatsNew, hasUnseenWhatsNew,
  theme, onToggleTheme,
}) {
  const [localSearch, setLocalSearch] = useState(search);
  const [showTrending, setShowTrending] = useState(false);
  const [trending, setTrending] = useState([]);
  const debounceRef = useRef(null);
  const searchRef = useRef(null);
  const trendingBlurTimeoutRef = useRef(null);
  const searchItemType = mode === "radio" ? "radio" : "tv";

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
    if (val.trim()) setShowTrending(false);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => onSearch(val), 350);
  };

  const handleFocus = useCallback(() => {
    clearTimeout(trendingBlurTimeoutRef.current);
    if (localSearch.trim()) return;
    setShowTrending(true);
    fetchTrending(searchItemType)
      .then((items) => setTrending(items || []))
      .catch(() => setTrending([]));
  }, [localSearch, searchItemType]);

  const handleBlur = () => {
    trendingBlurTimeoutRef.current = setTimeout(() => setShowTrending(false), 150);
  };

  const handleTrendingPick = (item) => {
    clearTimeout(trendingBlurTimeoutRef.current);
    setLocalSearch(item.name);
    onSearch(item.name);
    setShowTrending(false);
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
          <button className={`mode-btn ${mode === "tv" ? "active" : ""}`} onClick={() => onModeSwitch("tv")} aria-label="Television" title="Television">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="7" width="20" height="15" rx="2" ry="2" /><polyline points="17 2 12 7 7 2" />
            </svg>
            <span className="mode-btn-label">Television</span>
          </button>
          <button className={`mode-btn ${mode === "radio" ? "active" : ""}`} onClick={() => onModeSwitch("radio")} aria-label="Radio" title="Radio">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="2" />
              <path d="M16.24 7.76a6 6 0 0 1 0 8.49" />
              <path d="M7.76 16.24a6 6 0 0 1 0-8.49" />
            </svg>
            <span className="mode-btn-label">Radio</span>
          </button>
          <button className={`mode-btn ${mode === "map" ? "active" : ""}`} onClick={() => onModeSwitch("map")} aria-label="Map" title="Map">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="2" y1="12" x2="22" y2="12" />
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
            <span className="mode-btn-label">Map</span>
          </button>
        </div>
      </div>

      <div className="header-right">
        {isGuest ? (
          <button
            type="button"
            className="header-fav-btn header-fav-btn--guest"
            onClick={() => onGuestNotice?.("Sign in to view and save favorites.")}
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
            onFocus={handleFocus}
            onBlur={handleBlur}
            aria-label={mode === "tv" ? "Search channels" : "Search stations"}
          />
          {showTrending && trending.length > 0 && (
            <div className="trending-dropdown" role="listbox" aria-label="Trending">
              <div className="trending-dropdown-label">Trending now</div>
              {trending.map((item) => (
                <button
                  type="button"
                  key={item.id}
                  className="trending-dropdown-item"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => handleTrendingPick(item)}
                >
                  {item.logo ? (
                    <img src={item.logo} alt="" className="trending-dropdown-logo" />
                  ) : (
                    <span className="trending-dropdown-logo trending-dropdown-logo--placeholder" />
                  )}
                  <span className="trending-dropdown-name">{item.name}</span>
                </button>
              ))}
            </div>
          )}
          <button
            type="button"
            className="ai-search-btn ai-search-btn--inline"
            onClick={onOpenAISearch}
            aria-label="Search with AI instead"
            title="Search with AI instead"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L14.09 8.26L20 9.27L15.55 13.97L16.91 20L12 16.9L7.09 20L8.45 13.97L4 9.27L9.91 8.26L12 2Z" fill="currentColor" />
            </svg>
          </button>
        </div>
        <button
          className="whats-new-btn"
          onClick={onOpenWhatsNew}
          aria-label="What's new"
          title="What's new"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20.59 13.41 13.41 20.59a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82Z" />
            <circle cx="7" cy="7" r="1" fill="currentColor" stroke="none" />
          </svg>
          {hasUnseenWhatsNew && <span className="whats-new-dot" aria-hidden="true" />}
        </button>
        <button
          className="theme-toggle-btn"
          onClick={onToggleTheme}
          aria-label={theme === "light" ? "Switch to dark theme" : "Switch to light theme"}
          title={theme === "light" ? "Switch to dark theme" : "Switch to light theme"}
        >
          {theme === "light" ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z" />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          )}
        </button>
      </div>
      <div className="header-user">
        <UserMenu user={user} onLogin={onLogin} onLogout={onLogout} onOpenAdmin={onOpenAdmin} />
      </div>
    </header>
  );
}
