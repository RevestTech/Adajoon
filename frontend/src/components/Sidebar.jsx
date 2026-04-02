import { useState, useMemo } from "react";

const INITIAL_VISIBLE = 12;

export default function Sidebar({
  mode,
  className,
  railCollapsed = false,
  onToggleRail,
  categories,
  countries,
  activeCategories = [],
  activeCountries = [],
  onSelectCategory,
  onSelectCountry,
  favoritesCount,
  showFavorites,
  onToggleFavorites,
  radioTags,
  radioCountries,
  activeTags = [],
  onSelectTag,
  isGuest,
  onLogin,
  onGuestNotice,
}) {
  const [tab, setTab] = useState("categories");
  const [radioTab, setRadioTab] = useState("genres");
  const [filterText, setFilterText] = useState("");
  const [expanded, setExpanded] = useState(false);
  const [sortBy, setSortBy] = useState("name");

  const lowerFilter = filterText.toLowerCase();

  const sortItems = (items, getName, getCount) => {
    const sorted = [...items];
    if (sortBy === "name") sorted.sort((a, b) => getName(a).localeCompare(getName(b)));
    else if (sortBy === "count") sorted.sort((a, b) => getCount(b) - getCount(a));
    return sorted;
  };

  const filteredCategories = useMemo(
    () => sortItems(
      categories.filter((c) => c.name.toLowerCase().includes(lowerFilter)),
      (c) => c.name, (c) => c.channel_count
    ),
    [categories, lowerFilter, sortBy]
  );
  const filteredCountries = useMemo(
    () => sortItems(
      countries.filter((c) => c.name.toLowerCase().includes(lowerFilter) || c.code.toLowerCase().includes(lowerFilter)),
      (c) => c.name, (c) => c.channel_count
    ),
    [countries, lowerFilter, sortBy]
  );
  const filteredRadioTags = useMemo(
    () => sortItems(
      radioTags.filter((t) => t.name.toLowerCase().includes(lowerFilter)),
      (t) => t.name, (t) => t.station_count
    ),
    [radioTags, lowerFilter, sortBy]
  );
  const filteredRadioCountries = useMemo(
    () => sortItems(
      radioCountries.filter((c) => c.country.toLowerCase().includes(lowerFilter) || c.country_code.toLowerCase().includes(lowerFilter)),
      (c) => c.country, (c) => c.station_count
    ),
    [radioCountries, lowerFilter, sortBy]
  );

  const handleTabChange = (t) => {
    setTab(t);
    setFilterText("");
    setExpanded(false);
  };
  const handleRadioTabChange = (t) => {
    setRadioTab(t);
    setFilterText("");
    setExpanded(false);
  };

  const placeholder = mode === "radio"
    ? (radioTab === "genres" ? "Filter genres..." : "Filter countries...")
    : (tab === "categories" ? "Filter categories..." : "Filter countries...");

  const showAll = expanded || filterText;

  const shellClass = `sidebar${railCollapsed ? " sidebar--rail-collapsed" : ""}`;

  const railToggle =
    typeof onToggleRail === "function" ? (
      <button
        type="button"
        className={`sidebar-edge-toggle${railCollapsed ? " sidebar-edge-toggle--collapsed" : ""}`}
        onClick={onToggleRail}
        aria-label={railCollapsed ? "Show filters" : "Hide filters"}
        title={railCollapsed ? "Show filters" : "Hide filters"}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.25" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          {railCollapsed ? (
            <polyline points="9 18 15 12 9 6" />
          ) : (
            <polyline points="15 18 9 12 15 6" />
          )}
        </svg>
      </button>
    ) : null;

  if (mode === "radio") {
    return (
      <div className={`sidebar-wrap ${className || ""}`.trim()}>
      <aside className={shellClass}>
        <div className="sidebar-body">
        <div className="sidebar-section">
          {isGuest ? (
            <div
              className="sidebar-item favorites-item favorites-item--guest"
              onClick={() => {
                onGuestNotice?.("Sign in to save favorites and sync across devices.");
                onLogin?.();
              }}
              onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onGuestNotice?.("Sign in to save favorites and sync across devices."); onLogin?.(); } }}
              tabIndex={0}
              role="button"
              title="Sign in to use favorites"
            >
              <span className="favorites-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                </svg>
                Favorites
              </span>
              <span className="favorites-guest-badge">Sign in</span>
            </div>
          ) : (
            <div
              className={`sidebar-item favorites-item ${showFavorites ? "active" : ""}`}
              onClick={onToggleFavorites}
              onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onToggleFavorites(); } }}
              tabIndex={0}
              role="button"
            >
              <span className="favorites-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill={showFavorites ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                </svg>
                Favorites
              </span>
              {favoritesCount > 0 && (
                <span className="sidebar-count favorites-count">{favoritesCount}</span>
              )}
            </div>
          )}
        </div>

        <div className="sidebar-tabs">
          <TabButton active={radioTab === "genres"} onClick={() => handleRadioTabChange("genres")}>Genres</TabButton>
          <TabButton active={radioTab === "countries"} onClick={() => handleRadioTabChange("countries")}>Countries</TabButton>
        </div>

        <div className="sidebar-toolbar">
          <SidebarSearch value={filterText} onChange={setFilterText} placeholder={placeholder} />
          <SortToggle sortBy={sortBy} onChange={setSortBy} />
        </div>

        {radioTab === "genres" && (
          <SidebarList
            items={filteredRadioTags}
            activeIds={activeTags}
            onSelect={onSelectTag}
            getId={(t) => t.name}
            getLabel={(t) => t.name}
            getCount={(t) => t.station_count}
            allLabel="All Genres"
            emptyMsg={`No genres match "${filterText}"`}
            showAll={showAll}
            expanded={expanded}
            onToggleExpand={() => setExpanded((v) => !v)}
            filterText={filterText}
          />
        )}

        {radioTab === "countries" && (
          <SidebarList
            items={filteredRadioCountries}
            activeIds={activeCountries}
            onSelect={onSelectCountry}
            getId={(c) => c.country_code}
            getLabel={(c) => c.country}
            getCount={(c) => c.station_count}
            allLabel="All Countries"
            emptyMsg={`No countries match "${filterText}"`}
            showAll={showAll}
            expanded={expanded}
            onToggleExpand={() => setExpanded((v) => !v)}
            filterText={filterText}
          />
        )}
        </div>
      </aside>
      {railToggle}
      </div>
    );
  }

  return (
    <div className={`sidebar-wrap ${className || ""}`.trim()}>
    <aside className={shellClass}>
      <div className="sidebar-body">
      <div className="sidebar-section">
        {isGuest ? (
          <div
            className="sidebar-item favorites-item favorites-item--guest"
            onClick={() => {
              onGuestNotice?.("Sign in to save favorites and sync across devices.");
              onLogin?.();
            }}
            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onGuestNotice?.("Sign in to save favorites and sync across devices."); onLogin?.(); } }}
            tabIndex={0}
            role="button"
            title="Sign in to use favorites"
          >
            <span className="favorites-label">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
              </svg>
              Favorites
            </span>
            <span className="favorites-guest-badge">Sign in</span>
          </div>
        ) : (
          <div
            className={`sidebar-item favorites-item ${showFavorites ? "active" : ""}`}
            onClick={onToggleFavorites}
            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onToggleFavorites(); } }}
            tabIndex={0}
            role="button"
          >
            <span className="favorites-label">
              <svg width="16" height="16" viewBox="0 0 24 24" fill={showFavorites ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
              </svg>
              Favorites
            </span>
            {favoritesCount > 0 && (
              <span className="sidebar-count favorites-count">{favoritesCount}</span>
            )}
          </div>
        )}
      </div>

      <div className="sidebar-tabs">
        <TabButton active={tab === "categories"} onClick={() => handleTabChange("categories")}>Categories</TabButton>
        <TabButton active={tab === "countries"} onClick={() => handleTabChange("countries")}>Countries</TabButton>
      </div>

      <div className="sidebar-toolbar">
        <SidebarSearch value={filterText} onChange={setFilterText} placeholder={placeholder} />
        <SortToggle sortBy={sortBy} onChange={setSortBy} />
      </div>

      {tab === "categories" && (
        <SidebarList
          items={filteredCategories}
          activeIds={activeCategories}
          onSelect={(id) => { onSelectCategory(id); }}
          getId={(c) => c.id}
          getLabel={(c) => c.name}
          getCount={(c) => c.channel_count}
          getLiveCount={(c) => c.live_count ?? 0}
          getVerifiedCount={(c) => c.verified_count ?? 0}
          allLabel="All"
          emptyMsg={`No categories match "${filterText}"`}
          showAll={showAll}
          expanded={expanded}
          onToggleExpand={() => setExpanded((v) => !v)}
          filterText={filterText}
        />
      )}

      {tab === "countries" && (
        <SidebarList
          items={filteredCountries}
          activeIds={activeCountries}
          onSelect={(code) => { onSelectCountry(code); }}
          getId={(c) => c.code}
          getLabel={(c) => c.name}
          getCount={(c) => c.channel_count}
          getLiveCount={(c) => c.live_count ?? 0}
          getVerifiedCount={(c) => c.verified_count ?? 0}
          allLabel="All"
          emptyMsg={`No countries match "${filterText}"`}
          showAll={showAll}
          expanded={expanded}
          onToggleExpand={() => setExpanded((v) => !v)}
          filterText={filterText}
        />
      )}
      </div>
    </aside>
    {railToggle}
    </div>
  );
}

function SidebarList({
  items,
  activeIds = [],
  onSelect,
  getId,
  getLabel,
  getCount,
  getLiveCount,
  getVerifiedCount,
  allLabel,
  emptyMsg,
  showAll,
  expanded,
  onToggleExpand,
  filterText,
}) {
  const visible = showAll ? items : items.slice(0, INITIAL_VISIBLE);
  const hasMore = items.length > INITIAL_VISIBLE;
  const hasSelection = activeIds.length > 0;
  const showTvHealth = typeof getLiveCount === "function" && typeof getVerifiedCount === "function";

  const handleKey = (e, cb) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); cb(); } };

  return (
    <div className="sidebar-list-section">
      <div className="sidebar-filter-list" role="listbox" aria-multiselectable="true">
        {!filterText && (
          <div
            className={`sidebar-item sidebar-item--all ${!hasSelection ? "active" : ""}`}
            onClick={() => onSelect(null)}
            onKeyDown={(e) => handleKey(e, () => onSelect(null))}
            tabIndex={0}
            role="option"
            aria-selected={!hasSelection}
          >
            <span className="sidebar-check" aria-hidden />
            <span className="sidebar-item-label">{allLabel}</span>
          </div>
        )}
        {visible.map((item) => {
          const id = getId(item);
          const isActive = activeIds.includes(id);
          return (
            <div
              key={id}
              className={`sidebar-item ${isActive ? "active" : ""}`}
              onClick={() => onSelect(id)}
              onKeyDown={(e) => handleKey(e, () => onSelect(id))}
              tabIndex={0}
              role="option"
              aria-selected={isActive}
            >
              <span className="sidebar-check">{isActive ? "✓" : ""}</span>
              <span className="sidebar-item-label">{getLabel(item)}</span>
              {showTvHealth ? (
                <div
                  className="sidebar-count-group"
                  title={`Total ${getCount(item).toLocaleString()} · Live ${getLiveCount(item).toLocaleString()} · Verified ${getVerifiedCount(item).toLocaleString()}`}
                >
                  <span className="sidebar-count sidebar-count--total">{getCount(item).toLocaleString()}</span>
                  <span className="sidebar-chip sidebar-chip--live" title="Live (playable stream)">
                    L {getLiveCount(item).toLocaleString()}
                  </span>
                  <span className="sidebar-chip sidebar-chip--ver" title="Verified">
                    ✓ {getVerifiedCount(item).toLocaleString()}
                  </span>
                </div>
              ) : (
                <span className="sidebar-count">{getCount(item).toLocaleString()}</span>
              )}
            </div>
          );
        })}
      </div>
      {filterText && items.length === 0 && (
        <div className="sidebar-empty">{emptyMsg}</div>
      )}
      {!filterText && hasMore && (
        <button className="sidebar-list-expand" onClick={onToggleExpand}>
          {expanded ? "Show less" : `Show all ${items.length}`}
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ transform: expanded ? "rotate(180deg)" : "none", transition: "transform 0.2s" }}>
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>
      )}
    </div>
  );
}

function SidebarSearch({ value, onChange, placeholder }) {
  return (
    <div className="sidebar-search">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
      </svg>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
      {value && (
        <button onClick={() => onChange("")} className="sidebar-search-clear">×</button>
      )}
    </div>
  );
}

function SortToggle({ sortBy, onChange }) {
  return (
    <div className="sort-toggle">
      <button
        className={`sort-btn ${sortBy === "name" ? "active" : ""}`}
        onClick={() => onChange("name")}
        title="Sort A-Z"
      >
        A-Z
      </button>
      <button
        className={`sort-btn ${sortBy === "count" ? "active" : ""}`}
        onClick={() => onChange("count")}
        title="Sort by most channels"
      >
        #
      </button>
    </div>
  );
}

function TabButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`sidebar-tab-btn ${active ? "active" : ""}`}
    >
      {children}
    </button>
  );
}
