import { useState, useMemo } from "react";

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

  const lowerFilter = filterText.toLowerCase();

  const filteredCategories = useMemo(
    () => categories.filter((c) => c.name.toLowerCase().includes(lowerFilter)),
    [categories, lowerFilter]
  );

  const filteredCountries = useMemo(
    () => countries.filter((c) => c.name.toLowerCase().includes(lowerFilter) || c.code.toLowerCase().includes(lowerFilter)),
    [countries, lowerFilter]
  );

  const filteredRadioTags = useMemo(
    () => radioTags.filter((t) => t.name.toLowerCase().includes(lowerFilter)),
    [radioTags, lowerFilter]
  );

  const filteredRadioCountries = useMemo(
    () => radioCountries.filter((c) => c.country.toLowerCase().includes(lowerFilter) || c.country_code.toLowerCase().includes(lowerFilter)),
    [radioCountries, lowerFilter]
  );

  const handleTabChange = (t) => {
    setTab(t);
    setFilterText("");
  };

  const handleRadioTabChange = (t) => {
    setRadioTab(t);
    setFilterText("");
  };

  const placeholder = mode === "radio"
    ? (radioTab === "genres" ? "Filter genres..." : "Filter countries...")
    : (tab === "categories" ? "Filter categories..." : "Filter countries...");

  if (mode === "radio") {
    return (
      <aside className={`sidebar ${className || ""}`}>
        <div className="sidebar-section">
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

        <div style={{ display: "flex", gap: "4px", padding: "0 12px", marginBottom: "12px" }}>
          <TabButton active={radioTab === "genres"} onClick={() => handleRadioTabChange("genres")}>
            Genres
          </TabButton>
          <TabButton active={radioTab === "countries"} onClick={() => handleRadioTabChange("countries")}>
            Countries
          </TabButton>
        </div>

        <SidebarSearch value={filterText} onChange={setFilterText} placeholder={placeholder} />

        {radioTab === "genres" && (
          <div className="sidebar-section">
            {!filterText && (
              <div
                className={`sidebar-item ${!activeTag ? "active" : ""}`}
                onClick={() => onSelectTag(null)}
              >
                <span>All Genres</span>
              </div>
            )}
            {filteredRadioTags.map((t) => (
              <div
                key={t.name}
                className={`sidebar-item ${activeTag === t.name ? "active" : ""}`}
                onClick={() => onSelectTag(t.name)}
              >
                <span>{t.name}</span>
                <span className="sidebar-count">{t.station_count.toLocaleString()}</span>
              </div>
            ))}
            {filterText && filteredRadioTags.length === 0 && (
              <div className="sidebar-empty">No genres match "{filterText}"</div>
            )}
          </div>
        )}

        {radioTab === "countries" && (
          <div className="sidebar-section">
            {!filterText && (
              <div
                className={`sidebar-item ${!activeCountry ? "active" : ""}`}
                onClick={() => onSelectCountry(null)}
              >
                <span>All Countries</span>
              </div>
            )}
            {filteredRadioCountries.map((c) => (
              <div
                key={c.country_code}
                className={`sidebar-item ${activeCountry === c.country_code ? "active" : ""}`}
                onClick={() => onSelectCountry(c.country_code)}
              >
                <span>{c.country}</span>
                <span className="sidebar-count">{c.station_count.toLocaleString()}</span>
              </div>
            ))}
            {filterText && filteredRadioCountries.length === 0 && (
              <div className="sidebar-empty">No countries match "{filterText}"</div>
            )}
          </div>
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

      <div style={{ display: "flex", gap: "4px", padding: "0 12px", marginBottom: "12px" }}>
        <TabButton active={tab === "categories"} onClick={() => handleTabChange("categories")}>
          Categories
        </TabButton>
        <TabButton active={tab === "countries"} onClick={() => handleTabChange("countries")}>
          Countries
        </TabButton>
      </div>

      <SidebarSearch value={filterText} onChange={setFilterText} placeholder={placeholder} />

      {tab === "categories" && (
        <div className="sidebar-section">
          {!filterText && (
            <div
              className={`sidebar-item ${!activeCategory && !showFavorites ? "active" : ""}`}
              onClick={() => onSelectCategory(null)}
            >
              <span>All Categories</span>
            </div>
          )}
          {filteredCategories.map((cat) => (
            <div
              key={cat.id}
              className={`sidebar-item ${activeCategory === cat.id ? "active" : ""}`}
              onClick={() => onSelectCategory(cat.id)}
            >
              <span>{cat.name}</span>
              <span className="sidebar-count">{cat.channel_count}</span>
            </div>
          ))}
          {filterText && filteredCategories.length === 0 && (
            <div className="sidebar-empty">No categories match "{filterText}"</div>
          )}
        </div>
      )}

      {tab === "countries" && (
        <div className="sidebar-section">
          {!filterText && (
            <div
              className={`sidebar-item ${!activeCountry && !showFavorites ? "active" : ""}`}
              onClick={() => onSelectCountry(null)}
            >
              <span>All Countries</span>
            </div>
          )}
          {filteredCountries.map((c) => (
            <div
              key={c.code}
              className={`sidebar-item ${activeCountry === c.code ? "active" : ""}`}
              onClick={() => onSelectCountry(c.code)}
            >
              <span>
                {c.flag && <span className="country-flag">{c.flag}</span>}
                {c.name}
              </span>
              <span className="sidebar-count">{c.channel_count}</span>
            </div>
          ))}
          {filterText && filteredCountries.length === 0 && (
            <div className="sidebar-empty">No countries match "{filterText}"</div>
          )}
        </div>
      )}
    </aside>
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

function TabButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      style={{
        flex: 1,
        padding: "8px 12px",
        background: active ? "rgba(233,69,96,0.15)" : "transparent",
        border: "1px solid " + (active ? "var(--accent)" : "var(--border)"),
        borderRadius: "var(--radius-sm)",
        color: active ? "var(--accent)" : "var(--text-secondary)",
        cursor: "pointer",
        fontSize: "12px",
        fontWeight: 600,
        fontFamily: "inherit",
        transition: "all 0.15s",
      }}
    >
      {children}
    </button>
  );
}
