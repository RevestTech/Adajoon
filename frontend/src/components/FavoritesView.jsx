export default function FavoritesView({
  tvFavorites,
  radioFavorites,
  onSelectChannel,
  onSelectStation,
  isTvFavorite,
  isRadioFavorite,
  onToggleTvFavorite,
  onToggleRadioFavorite,
  onClearFavorites,
}) {
  const hasTv = tvFavorites.length > 0;
  const hasRadio = radioFavorites.length > 0;
  const totalCount = tvFavorites.length + radioFavorites.length;

  return (
    <>
      <div className="content-header">
        <div>
          <h2 className="content-title">Favorites</h2>
          <span className="content-subtitle">{totalCount} saved</span>
        </div>
      </div>

      <div className="content-body">
        <div className="active-filters">
          <span className="filter-tag" onClick={onClearFavorites}>Favorites ✕</span>
        </div>

        {!hasTv && !hasRadio ? (
        <div className="empty-state">
          <h3>No favorites yet</h3>
          <p>Click the heart icon on any channel or station to add it to your favorites.</p>
        </div>
      ) : (
        <div className="favorites-columns">
          <div className="favorites-col">
            <div className="favorites-col-header">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="2" y="7" width="20" height="15" rx="2" ry="2" /><polyline points="17 2 12 7 7 2" />
              </svg>
              TV Channels
              <span className="favorites-col-count">{tvFavorites.length}</span>
            </div>
            {hasTv ? (
              <div className="favorites-col-list">
                {tvFavorites.map((ch) => (
                  <div key={ch.id} className="fav-row" onClick={() => onSelectChannel(ch)}>
                    <div className="fav-row-logo">
                      {ch.logo ? (
                        <img src={ch.logo} alt={ch.name} loading="lazy" onError={(e) => { e.target.style.display = "none"; e.target.nextSibling.style.display = "flex"; }} />
                      ) : null}
                      <div className="fav-row-logo-placeholder" style={ch.logo ? { display: "none" } : {}}>
                        {ch.name?.charAt(0)?.toUpperCase() || "?"}
                      </div>
                    </div>
                    <div className="fav-row-info">
                      <span className="fav-row-name">{ch.name}</span>
                      <div className="fav-row-tags">
                        {ch.country_code && <span className="channel-tag">{ch.country_code}</span>}
                        {ch.categories && ch.categories.split(";").filter(Boolean).slice(0, 2).map((c) => (
                          <span key={c} className="channel-tag">{c}</span>
                        ))}
                      </div>
                    </div>
                    <button
                      className={`favorite-btn list-fav-btn ${isTvFavorite(ch.id) ? "favorited" : ""}`}
                      onClick={(e) => { e.stopPropagation(); onToggleTvFavorite(ch); }}
                      title="Remove from favorites"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="favorites-col-empty">No TV channels saved</div>
            )}
          </div>

          <div className="favorites-col">
            <div className="favorites-col-header">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="2" />
                <path d="M16.24 7.76a6 6 0 0 1 0 8.49" />
                <path d="M7.76 16.24a6 6 0 0 1 0-8.49" />
              </svg>
              Radio Stations
              <span className="favorites-col-count">{radioFavorites.length}</span>
            </div>
            {hasRadio ? (
              <div className="favorites-col-list">
                {radioFavorites.map((st) => {
                  const tags = st.tags ? st.tags.split(",").map((t) => t.trim()).filter(Boolean) : [];
                  return (
                    <div key={st.id} className="fav-row" onClick={() => onSelectStation(st)}>
                      <div className="fav-row-logo">
                        {st.favicon ? (
                          <img src={st.favicon} alt={st.name} loading="lazy" onError={(e) => { e.target.style.display = "none"; e.target.nextSibling.style.display = "flex"; }} />
                        ) : null}
                        <div className="fav-row-logo-placeholder radio-placeholder" style={st.favicon ? { display: "none" } : {}}>
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="12" cy="12" r="2" />
                            <path d="M16.24 7.76a6 6 0 0 1 0 8.49" />
                            <path d="M7.76 16.24a6 6 0 0 1 0-8.49" />
                          </svg>
                        </div>
                      </div>
                      <div className="fav-row-info">
                        <span className="fav-row-name">{st.name}</span>
                        <div className="fav-row-tags">
                          {st.country_code && <span className="channel-tag">{st.country_code}</span>}
                          {tags.slice(0, 2).map((t) => (
                            <span key={t} className="channel-tag">{t}</span>
                          ))}
                        </div>
                      </div>
                      <button
                        className={`favorite-btn list-fav-btn ${isRadioFavorite(st.id) ? "favorited" : ""}`}
                        onClick={(e) => { e.stopPropagation(); onToggleRadioFavorite(st); }}
                        title="Remove from favorites"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                        </svg>
                      </button>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="favorites-col-empty">No radio stations saved</div>
            )}
          </div>
        </div>
      )}
      </div>
    </>
  );
}
