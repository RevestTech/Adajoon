import ViewToggle from "./ViewToggle";
import VoteIndicator from "./VoteIndicator";

const GUEST_LIMIT = 20;

/** Maps channel health_status to badge classes, dot class, label, and thumb overlay class. */
function getTvStreamStatus(healthStatus) {
  const s = healthStatus || "unknown";
  if (s === "verified") {
    return {
      badgeClass: "channel-stream-badge badge-verified status-verified",
      dotClass: "verified",
      label: "VERIFIED",
      thumbClass: "",
    };
  }
  if (s === "online" || s === "manifest_only") {
    return {
      badgeClass: "channel-stream-badge badge-manifest status-live-partial",
      dotClass: s === "manifest_only" ? "manifest_only" : "online",
      label: "LIVE",
      thumbClass: "partial",
    };
  }
  if (s === "offline") {
    return {
      badgeClass: "channel-stream-badge status-offline",
      dotClass: "offline",
      label: "OFFLINE",
      thumbClass: "down",
    };
  }
  if (s === "timeout") {
    return {
      badgeClass: "channel-stream-badge status-timeout",
      dotClass: "timeout",
      label: "SLOW",
      thumbClass: "slow",
    };
  }
  if (s === "error") {
    return {
      badgeClass: "channel-stream-badge status-neutral",
      dotClass: "error",
      label: "ERROR",
      thumbClass: "neutral",
    };
  }
  if (s === "geo_blocked") {
    return {
      badgeClass: "channel-stream-badge status-neutral",
      dotClass: "geo_blocked",
      label: "GEO BLOCKED",
      thumbClass: "neutral",
    };
  }
  return {
    badgeClass: "channel-stream-badge status-neutral",
    dotClass: "unknown",
    label: "UNKNOWN",
    thumbClass: "neutral",
  };
}

const QUALITY_OPTIONS = [
  { key: "all", label: "All" },
  { key: "has_stream", label: "Has Stream", dot: "online" },
  { key: "verified", label: "Verified", dot: "verified" },
  { key: "live", label: "Live", dot: "online" },
  { key: "hide_dead", label: "Hide Dead", dot: "offline" },
];

export default function ChannelGrid({
  channels,
  loading,
  error,
  total,
  page,
  totalPages,
  onPageChange,
  onSelect,
  activeCategories = [],
  activeCountries = [],
  search,
  showFavorites,
  activeQualities = [],
  onQualityChange,
  onClearFilter,
  onRetry,
  isFavorite,
  onToggleFavorite,
  viewMode,
  onViewToggle,
  isGuest,
  onLogin,
  getVoteSummary,
  stats,
}) {
  const hasFilters = activeCategories.length > 0 || activeCountries.length > 0 || search || showFavorites || activeQualities.length > 0;

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
      : activeCategories.length > 0 || activeCountries.length > 0
        ? "Filtered Channels"
        : "All Channels";

  return (
    <>
      <div className="content-header">
        <div className="content-title-row">
          <div>
            <h2 className="content-title">{title}</h2>
            <span className="content-subtitle">
              {total.toLocaleString()} {showFavorites ? "saved" : ""} channel{total !== 1 ? "s" : ""}{!showFavorites ? " found" : ""}
            </span>
          </div>
          {stats && (
            <div className="content-stats">
              <span className="stat-pill">{stats.total_channels?.toLocaleString()} <small>channels</small></span>
              <span className="stat-pill">{stats.total_radio_stations?.toLocaleString()} <small>radio</small></span>
              <span className="stat-pill">{stats.total_countries?.toLocaleString()} <small>countries</small></span>
            </div>
          )}
        </div>
        <div className="content-toolbar">
          <div className="quality-filter">
            {QUALITY_OPTIONS.map((opt) => {
              const val = opt.key === "hide_dead" ? "hide_offline" : opt.key;
              const active = opt.key === "all" ? activeQualities.length === 0 : activeQualities.includes(val);
              return (
                <button
                  key={opt.key}
                  className={`quality-btn ${active ? "active" : ""}`}
                  onClick={() => onQualityChange(opt.key)}
                >
                  {opt.dot && <span className={`status-dot ${opt.dot}`} />}
                  {opt.label}
                </button>
              );
            })}
          </div>
          <ViewToggle viewMode={viewMode} onViewToggle={onViewToggle} />
        </div>
      </div>

      <div className="content-body">
        {hasFilters && (
          <div className="active-filters">
            {showFavorites && (
              <span className="filter-tag" onClick={() => onClearFilter("favorites")}>
                Favorites ✕
              </span>
            )}
            {activeQualities.map((q) => {
              const opt = QUALITY_OPTIONS.find((o) => (o.key === "hide_dead" ? "hide_offline" : o.key) === q);
              return (
                <span key={q} className="filter-tag" onClick={() => onClearFilter("quality", q)}>
                  {opt ? opt.label : q} ✕
                </span>
              );
            })}
            {search && (
              <span className="filter-tag" onClick={() => onClearFilter("search")}>
                Search: {search} ✕
              </span>
            )}
            {activeCategories.map((cat) => (
              <span key={cat} className="filter-tag" onClick={() => onClearFilter("category", cat)}>
                {cat} ✕
              </span>
            ))}
            {activeCountries.map((code) => (
              <span key={code} className="filter-tag" onClick={() => onClearFilter("country", code)}>
                {code} ✕
              </span>
            ))}
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
            <div className={viewMode === "list" ? "channel-list" : viewMode === "thumb" ? "thumb-grid" : "channel-grid"}>
              {(isGuest ? channels.slice(0, GUEST_LIMIT) : channels).map((ch) => {
                const props = {
                  key: ch.id,
                  channel: ch,
                  onClick: () => onSelect(ch),
                  favorited: !isGuest && isFavorite(ch.id),
                  onToggleFavorite: isGuest ? (e) => { e.stopPropagation(); onLogin(); } : (e) => { e.stopPropagation(); onToggleFavorite(ch); },
                  isGuest,
                  voteSummary: getVoteSummary ? getVoteSummary(ch.id) : {},
                };
                if (viewMode === "list") return <ChannelRow {...props} />;
                if (viewMode === "thumb") return <ChannelThumb {...props} />;
                return <ChannelCard {...props} />;
              })}
            </div>

            {isGuest && channels.length > GUEST_LIMIT && (
              <GuestBanner onLogin={onLogin} total={total} type="channels" />
            )}

            {!isGuest && !showFavorites && totalPages > 1 && (
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
      </div>
    </>
  );
}

function GuestBanner({ onLogin, total, type }) {
  return (
    <div className="guest-banner">
      <div className="guest-banner-content">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
          <polyline points="10 17 15 12 10 7" />
          <line x1="15" y1="12" x2="3" y2="12" />
        </svg>
        <div>
          <strong>Sign in to unlock all {total.toLocaleString()} {type}</strong>
          <span>Plus save favorites and sync across devices</span>
        </div>
        <button onClick={onLogin}>Sign In</button>
      </div>
    </div>
  );
}

function ChannelCard({ channel, onClick, favorited, onToggleFavorite, isGuest, voteSummary }) {
  const cats = channel.categories ? channel.categories.split(";").filter(Boolean) : [];
  const streamStatus = channel.stream_url ? getTvStreamStatus(channel.health_status) : null;

  return (
    <div className="channel-card" onClick={onClick}>
      {!isGuest && (
        <button
          className={`favorite-btn ${favorited ? "favorited" : ""}`}
          onClick={onToggleFavorite}
          title={favorited ? "Remove from favorites" : "Add to favorites"}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill={favorited ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
          </svg>
        </button>
      )}
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
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <rect x="2" y="7" width="20" height="15" rx="2" ry="2" /><polyline points="17 2 12 7 7 2" />
        </svg>
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
        {streamStatus && (
          <span className={streamStatus.badgeClass}>
            <span className={`status-dot ${streamStatus.dotClass}`} />
            {streamStatus.label}
          </span>
        )}
        <VoteIndicator summary={voteSummary} />
      </div>
    </div>
  );
}

function ChannelRow({ channel, onClick, favorited, onToggleFavorite, isGuest, voteSummary }) {
  const cats = channel.categories ? channel.categories.split(";").filter(Boolean) : [];
  const streamStatus = channel.stream_url ? getTvStreamStatus(channel.health_status) : null;

  return (
    <div className="list-row" onClick={onClick}>
      <div className="list-row-logo">
        {channel.logo ? (
          <img
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
          className="list-row-logo-placeholder"
          style={channel.logo ? { display: "none" } : {}}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="7" width="20" height="15" rx="2" ry="2" /><polyline points="17 2 12 7 7 2" />
          </svg>
        </div>
      </div>
      <div className="list-row-info">
        <span className="list-row-name">{channel.name}</span>
        <div className="list-row-tags">
          {channel.country_code && <span className="channel-tag">{channel.country_code}</span>}
          {cats.slice(0, 3).map((c) => (
            <span key={c} className="channel-tag">{c}</span>
          ))}
        </div>
      </div>
      <div className="list-row-actions">
        <VoteIndicator summary={voteSummary} />
        {streamStatus && (
          <span className={streamStatus.badgeClass}>
            <span className={`status-dot ${streamStatus.dotClass}`} />
            {streamStatus.label}
          </span>
        )}
        {!isGuest && (
          <button
            className={`favorite-btn list-fav-btn ${favorited ? "favorited" : ""}`}
            onClick={onToggleFavorite}
            title={favorited ? "Remove from favorites" : "Add to favorites"}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill={favorited ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}

function ChannelThumb({ channel, onClick, favorited, onToggleFavorite, isGuest, voteSummary }) {
  const cats = channel.categories ? channel.categories.split(";").filter(Boolean) : [];
  const streamStatus = channel.stream_url ? getTvStreamStatus(channel.health_status) : null;

  return (
    <div className="thumb-card" onClick={onClick}>
      <div className="thumb-image">
        {channel.logo ? (
          <img
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
          className="thumb-placeholder"
          style={channel.logo ? { display: "none" } : {}}
        >
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="7" width="20" height="15" rx="2" ry="2" /><polyline points="17 2 12 7 7 2" />
          </svg>
        </div>
        {streamStatus && (
          <span className={`thumb-status ${streamStatus.thumbClass}`.trim()}>
            <span className={`status-dot ${streamStatus.dotClass}`} />
            {streamStatus.label}
          </span>
        )}
        {!isGuest && (
          <button
            className={`favorite-btn thumb-fav ${favorited ? "favorited" : ""}`}
            onClick={onToggleFavorite}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill={favorited ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
          </button>
        )}
      </div>
      <div className="thumb-info">
        <span className="thumb-name" title={channel.name}>{channel.name}</span>
        <div className="thumb-tags">
          {channel.country_code && <span className="channel-tag">{channel.country_code}</span>}
          {cats.slice(0, 2).map((c) => (
            <span key={c} className="channel-tag">{c}</span>
          ))}
          <VoteIndicator summary={voteSummary} />
        </div>
      </div>
    </div>
  );
}
