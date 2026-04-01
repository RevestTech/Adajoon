import { useState, useMemo } from "react";

const INITIAL_VISIBLE = 12;

export default function Sidebar({
  mode,
  className,
  categories,
  countries,
  activeCategory,
  activeCountry,
  onSelectCategory,
  onSelectCountry,
  favoritesCount,
  showFavorites,
  onToggleFavorites,
  liveOnly,
  onToggleLiveOnly,
  radioTags,
  radioCountries,
  activeTag,
  onSelectTag,
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

  if (mode === "radio") {
    return (
      <aside className={`sidebar ${className || ""}`}>
        <div className="sidebar-section">
          <div
            className={`sidebar-item favorites-item ${showFavorites ? "active" : ""}`}
            onClick={onToggleFavorites}
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
          <div
            className={`sidebar-item live-filter-item ${liveOnly ? "active" : ""}`}
            onClick={onToggleLiveOnly}
          >
            <span className="live-filter-label">
              <span className={`live-dot ${liveOnly ? "on" : ""}`} />
              Working Stations Only
            </span>
            <span className={`live-filter-status ${liveOnly ? "on" : ""}`}>
              {liveOnly ? "ON" : "OFF"}
            </span>
          </div>
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
            activeId={activeTag}
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
            activeId={activeCountry}
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
      </aside>
    );
  }

  return (
    <aside className={`sidebar ${className || ""}`}>
      <div className="sidebar-section">
        <div
          className={`sidebar-item favorites-item ${showFavorites ? "active" : ""}`}
          onClick={onToggleFavorites}
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
        <div
          className={`sidebar-item live-filter-item ${liveOnly ? "active" : ""}`}
          onClick={onToggleLiveOnly}
        >
          <span className="live-filter-label">
            <span className={`live-dot ${liveOnly ? "on" : ""}`} />
            Live Channels Only
          </span>
          <span className={`live-filter-status ${liveOnly ? "on" : ""}`}>
            {liveOnly ? "ON" : "OFF"}
          </span>
        </div>
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
          activeId={activeCategory}
          onSelect={(id) => { onSelectCategory(id); }}
          getId={(c) => c.id}
          getLabel={(c) => c.name}
          getCount={(c) => c.channel_count}
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
          activeId={activeCountry}
          onSelect={(code) => { onSelectCountry(code); }}
          getId={(c) => c.code}
          getLabel={(c) => c.name}
          getCount={(c) => c.channel_count}
          allLabel="All"
          emptyMsg={`No countries match "${filterText}"`}
          showAll={showAll}
          expanded={expanded}
          onToggleExpand={() => setExpanded((v) => !v)}
          filterText={filterText}
        />
      )}
    </aside>
  );
}

function SidebarList({ items, activeId, onSelect, getId, getLabel, getCount, allLabel, emptyMsg, showAll, expanded, onToggleExpand, filterText }) {
  const visible = showAll ? items : items.slice(0, INITIAL_VISIBLE);
  const hasMore = items.length > INITIAL_VISIBLE;

  return (
    <div className="sidebar-list-section">
      <div className="sidebar-filter-list">
        {!filterText && (
          <div
            className={`sidebar-item ${!activeId ? "active" : ""}`}
            onClick={() => onSelect(null)}
          >
            <span className="sidebar-item-label">{allLabel}</span>
          </div>
        )}
        {visible.map((item) => {
          const id = getId(item);
          return (
            <div
              key={id}
              className={`sidebar-item ${activeId === id ? "active" : ""}`}
              onClick={() => onSelect(id)}
            >
              <span className="sidebar-item-label">{getLabel(item)}</span>
              <span className="sidebar-count">{getCount(item).toLocaleString()}</span>
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
