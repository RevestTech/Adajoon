export default function ChannelGrid({
  channels,
  loading,
  error,
  total,
  page,
  totalPages,
  onPageChange,
  onSelect,
  activeCategory,
  activeCountry,
  search,
  showFavorites,
  liveOnly,
  onClearFilter,
  onRetry,
  isFavorite,
  onToggleFavorite,
}) {
  const hasFilters = activeCategory || activeCountry || search || showFavorites || liveOnly;

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner" />
        <span>Loading channels...</span>
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
      : activeCategory || activeCountry
        ? "Filtered Channels"
        : "All Channels";

  return (
    <>
      <div className="content-header">
        <div>
          <h2 className="content-title">{title}</h2>
          <span className="content-subtitle">
            {total.toLocaleString()} {showFavorites ? "saved" : ""} channel{total !== 1 ? "s" : ""}{!showFavorites ? " found" : ""}
          </span>
        </div>
      </div>

      {hasFilters && (
        <div className="active-filters">
          {showFavorites && (
            <span className="filter-tag" onClick={() => onClearFilter("favorites")}>
              Favorites ✕
            </span>
          )}
          {liveOnly && (
            <span className="filter-tag" onClick={() => onClearFilter("liveOnly")}>
              Live only ✕
            </span>
          )}
          {search && (
            <span className="filter-tag" onClick={() => onClearFilter("search")}>
              Search: {search} ✕
            </span>
          )}
          {activeCategory && (
            <span className="filter-tag" onClick={() => onClearFilter("category")}>
              Category: {activeCategory} ✕
            </span>
          )}
          {activeCountry && (
            <span className="filter-tag" onClick={() => onClearFilter("country")}>
              Country: {activeCountry} ✕
            </span>
          )}
        </div>
      )}

      {channels.length === 0 ? (
        <div className="empty-state">
          <h3>{showFavorites ? "No favorites yet" : "No channels found"}</h3>
          <p>
            {showFavorites
              ? "Click the heart icon on any channel to add it to your favorites."
              : "Try adjusting your search or filters, or wait for data sync to complete."}
          </p>
        </div>
      ) : (
        <>
          <div className="channel-grid">
            {channels.map((ch) => (
              <ChannelCard
                key={ch.id}
                channel={ch}
                onClick={() => onSelect(ch)}
                favorited={isFavorite(ch.id)}
                onToggleFavorite={(e) => { e.stopPropagation(); onToggleFavorite(ch); }}
              />
            ))}
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

function ChannelCard({ channel, onClick, favorited, onToggleFavorite }) {
  const cats = channel.categories ? channel.categories.split(";").filter(Boolean) : [];

  return (
    <div className="channel-card" onClick={onClick}>
      <button
        className={`favorite-btn ${favorited ? "favorited" : ""}`}
        onClick={onToggleFavorite}
        title={favorited ? "Remove from favorites" : "Add to favorites"}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill={favorited ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
        </svg>
      </button>
      {channel.logo ? (
        <img
          className="channel-logo"
          src={channel.logo}
          alt={channel.name}
          loading="lazy"
          onError={(e) => {
            e.target.style.display = "none";
            e.target.nextSibling.style.display = "flex";
          }}
        />
      ) : null}
      <div
        className="channel-logo-placeholder"
        style={channel.logo ? { display: "none" } : {}}
      >
        {channel.name.charAt(0).toUpperCase()}
      </div>
      <div className="channel-name" title={channel.name}>
        {channel.name}
      </div>
      <div className="channel-meta">
        {channel.country_code && (
          <span className="channel-tag">{channel.country_code}</span>
        )}
        {cats.slice(0, 2).map((c) => (
          <span key={c} className="channel-tag">{c}</span>
        ))}
        {channel.stream_url && (
          <span className="channel-stream-badge">LIVE</span>
        )}
      </div>
    </div>
  );
}
