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
  onClearFilter,
  onRetry,
}) {
  const hasFilters = activeCategory || activeCountry || search;

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

  return (
    <>
      <div className="content-header">
        <div>
          <h2 className="content-title">
            {search ? `Results for "${search}"` : activeCategory || activeCountry ? "Filtered Channels" : "All Channels"}
          </h2>
          <span className="content-subtitle">{total.toLocaleString()} channels found</span>
        </div>
      </div>

      {hasFilters && (
        <div className="active-filters">
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
          <h3>No channels found</h3>
          <p>Try adjusting your search or filters, or wait for data sync to complete.</p>
        </div>
      ) : (
        <>
          <div className="channel-grid">
            {channels.map((ch) => (
              <ChannelCard key={ch.id} channel={ch} onClick={() => onSelect(ch)} />
            ))}
          </div>

          {totalPages > 1 && (
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

function ChannelCard({ channel, onClick }) {
  const cats = channel.categories ? channel.categories.split(";").filter(Boolean) : [];

  return (
    <div className="channel-card" onClick={onClick}>
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
