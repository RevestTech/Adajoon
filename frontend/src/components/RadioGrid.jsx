import ViewToggle from "./ViewToggle";

export default function RadioGrid({
  stations,
  loading,
  error,
  total,
  page,
  totalPages,
  onPageChange,
  onSelect,
  activeTag,
  activeCountry,
  search,
  showFavorites,
  workingOnly,
  onClearFilter,
  onRetry,
  isFavorite,
  onToggleFavorite,
  viewMode,
  onViewToggle,
}) {
  const hasFilters = activeTag || activeCountry || search || showFavorites || workingOnly;

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner" />
        <span>Loading radio stations...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state">
        <h3>Connection Issue</h3>
        <p>{error}</p>
        <button
          onClick={onRetry}
          style={{
            marginTop: 16, padding: "10px 24px",
            background: "var(--accent)", border: "none",
            borderRadius: "var(--radius-sm)", color: "#fff",
            cursor: "pointer", fontSize: 14, fontFamily: "inherit",
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  const title = showFavorites
    ? "Favorites"
    : search
      ? `Results for "${search}"`
      : activeTag
        ? `Genre: ${activeTag}`
        : activeCountry
          ? "Filtered Stations"
          : "All Radio Stations";

  return (
    <>
      <div className="content-header">
        <div>
          <h2 className="content-title">{title}</h2>
          <span className="content-subtitle">
            {total.toLocaleString()} {showFavorites ? "saved" : ""} station{total !== 1 ? "s" : ""}{!showFavorites ? " found" : ""}
          </span>
        </div>
        <ViewToggle viewMode={viewMode} onViewToggle={onViewToggle} />
      </div>

      {hasFilters && (
        <div className="active-filters">
          {showFavorites && (
            <span className="filter-tag" onClick={() => onClearFilter("favorites")}>
              Favorites ✕
            </span>
          )}
          {workingOnly && (
            <span className="filter-tag" onClick={() => onClearFilter("workingOnly")}>
              Working only ✕
            </span>
          )}
          {search && (
            <span className="filter-tag" onClick={() => onClearFilter("search")}>
              Search: {search} ✕
            </span>
          )}
          {activeTag && (
            <span className="filter-tag" onClick={() => onClearFilter("tag")}>
              Genre: {activeTag} ✕
            </span>
          )}
          {activeCountry && (
            <span className="filter-tag" onClick={() => onClearFilter("country")}>
              Country: {activeCountry} ✕
            </span>
          )}
        </div>
      )}

      {stations.length === 0 ? (
        <div className="empty-state">
          <h3>{showFavorites ? "No favorite stations yet" : "No stations found"}</h3>
          <p>
            {showFavorites
              ? "Click the heart icon on any station to add it to your favorites."
              : "Try adjusting your search or filters, or wait for data sync to complete."}
          </p>
        </div>
      ) : (
        <>
          <div className={viewMode === "list" ? "channel-list" : viewMode === "thumb" ? "thumb-grid" : "channel-grid"}>
            {stations.map((st) => {
              const props = {
                key: st.id,
                station: st,
                onClick: () => onSelect(st),
                favorited: isFavorite(st.id),
                onToggleFavorite: (e) => { e.stopPropagation(); onToggleFavorite(st); },
              };
              if (viewMode === "list") return <RadioRow {...props} />;
              if (viewMode === "thumb") return <RadioThumb {...props} />;
              return <RadioCard {...props} />;
            })}
          </div>

          {!showFavorites && totalPages > 1 && (
            <div className="pagination">
              <button disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
                ← Prev
              </button>
              <span className="page-info">
                Page {page} of {totalPages}
              </span>
              <button disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </>
  );
}

function RadioCard({ station, onClick, favorited, onToggleFavorite }) {
  const tags = station.tags ? station.tags.split(",").map((t) => t.trim()).filter(Boolean) : [];

  return (
    <div className="channel-card radio-card" onClick={onClick}>
      <button
        className={`favorite-btn ${favorited ? "favorited" : ""}`}
        onClick={onToggleFavorite}
        title={favorited ? "Remove from favorites" : "Add to favorites"}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill={favorited ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
        </svg>
      </button>
      <div className="radio-icon-wrap">
        {station.favicon ? (
          <img
            className="channel-logo"
            src={station.favicon}
            alt={station.name}
            loading="lazy"
            onError={(e) => {
              e.target.style.display = "none";
              e.target.nextSibling.style.display = "flex";
            }}
          />
        ) : null}
        <div
          className="channel-logo-placeholder radio-placeholder"
          style={station.favicon ? { display: "none" } : {}}
        >
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="2" />
            <path d="M16.24 7.76a6 6 0 0 1 0 8.49" />
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
            <path d="M7.76 16.24a6 6 0 0 1 0-8.49" />
            <path d="M4.93 19.07a10 10 0 0 1 0-14.14" />
          </svg>
        </div>
      </div>
      <div className="channel-name" title={station.name}>
        {station.name}
      </div>
      <div className="channel-meta">
        {station.country_code && (
          <span className="channel-tag">{station.country_code}</span>
        )}
        {tags.slice(0, 2).map((t) => (
          <span key={t} className="channel-tag">{t}</span>
        ))}
        {station.bitrate > 0 && (
          <span className="channel-tag">{station.bitrate}k</span>
        )}
        <span className={`channel-stream-badge ${station.last_check_ok ? "status-online" : "status-offline"}`}>
          <span className={`status-dot ${station.last_check_ok ? "online" : "offline"}`} />
          {station.last_check_ok ? "ON AIR" : "DOWN"}
        </span>
      </div>
    </div>
  );
}

function RadioRow({ station, onClick, favorited, onToggleFavorite }) {
  const tags = station.tags ? station.tags.split(",").map((t) => t.trim()).filter(Boolean) : [];

  return (
    <div className="list-row" onClick={onClick}>
      <div className="list-row-logo">
        {station.favicon ? (
          <img
            src={station.favicon}
            alt={station.name}
            loading="lazy"
            onError={(e) => {
              e.target.style.display = "none";
              e.target.nextSibling.style.display = "flex";
            }}
          />
        ) : null}
        <div
          className="list-row-logo-placeholder radio-placeholder"
          style={station.favicon ? { display: "none" } : {}}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="2" />
            <path d="M16.24 7.76a6 6 0 0 1 0 8.49" />
            <path d="M7.76 16.24a6 6 0 0 1 0-8.49" />
          </svg>
        </div>
      </div>
      <div className="list-row-info">
        <span className="list-row-name">{station.name}</span>
        <div className="list-row-tags">
          {station.country_code && <span className="channel-tag">{station.country_code}</span>}
          {tags.slice(0, 3).map((t) => (
            <span key={t} className="channel-tag">{t}</span>
          ))}
          {station.bitrate > 0 && <span className="channel-tag">{station.bitrate}k</span>}
        </div>
      </div>
      <div className="list-row-status">
        <span className={`channel-stream-badge ${station.last_check_ok ? "status-online" : "status-offline"}`}>
          <span className={`status-dot ${station.last_check_ok ? "online" : "offline"}`} />
          {station.last_check_ok ? "ON AIR" : "DOWN"}
        </span>
      </div>
      <button
        className={`favorite-btn list-fav-btn ${favorited ? "favorited" : ""}`}
        onClick={onToggleFavorite}
        title={favorited ? "Remove from favorites" : "Add to favorites"}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill={favorited ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
        </svg>
      </button>
    </div>
  );
}

function RadioThumb({ station, onClick, favorited, onToggleFavorite }) {
  const tags = station.tags ? station.tags.split(",").map((t) => t.trim()).filter(Boolean) : [];

  return (
    <div className="thumb-card" onClick={onClick}>
      <div className="thumb-image">
        {station.favicon ? (
          <img
            src={station.favicon}
            alt={station.name}
            loading="lazy"
            onError={(e) => {
              e.target.style.display = "none";
              e.target.nextSibling.style.display = "flex";
            }}
          />
        ) : null}
        <div
          className="thumb-placeholder radio-placeholder"
          style={station.favicon ? { display: "none" } : {}}
        >
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="2" />
            <path d="M16.24 7.76a6 6 0 0 1 0 8.49" />
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
            <path d="M7.76 16.24a6 6 0 0 1 0-8.49" />
            <path d="M4.93 19.07a10 10 0 0 1 0-14.14" />
          </svg>
        </div>
        <span className={`thumb-status ${station.last_check_ok ? "" : "down"}`}>
          <span className={`status-dot ${station.last_check_ok ? "online" : "offline"}`} />
          {station.last_check_ok ? "ON AIR" : "DOWN"}
        </span>
        <button
          className={`favorite-btn thumb-fav ${favorited ? "favorited" : ""}`}
          onClick={onToggleFavorite}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill={favorited ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
          </svg>
        </button>
      </div>
      <div className="thumb-info">
        <span className="thumb-name" title={station.name}>{station.name}</span>
        <div className="thumb-tags">
          {station.country_code && <span className="channel-tag">{station.country_code}</span>}
          {tags.slice(0, 2).map((t) => (
            <span key={t} className="channel-tag">{t}</span>
          ))}
          {station.bitrate > 0 && <span className="channel-tag">{station.bitrate}k</span>}
        </div>
      </div>
    </div>
  );
}
