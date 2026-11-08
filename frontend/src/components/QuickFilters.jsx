export default function QuickFilters({ 
  mode, 
  onVerifiedOnly, 
  onLiveOnly, 
  onHighlyRated,
  activeFilters = [],
  stats 
}) {
  const isActive = (filter) => activeFilters.includes(filter);

  const filters = mode === 'tv' ? [
    {
      id: 'verified',
      icon: '✓',
      label: 'Verified Only',
      count: stats?.verified_count || 0,
      color: 'success',
      onClick: onVerifiedOnly,
    },
    {
      id: 'live',
      icon: '🔴',
      label: 'Live Now',
      count: stats?.live_count || 0,
      color: 'danger',
      onClick: onLiveOnly,
    },
    {
      id: 'highly_rated',
      icon: '⭐',
      label: 'Highly Rated',
      count: stats?.top_rated_count || 0,
      color: 'warning',
      onClick: onHighlyRated,
    },
  ] : [
    {
      id: 'verified',
      icon: '✓',
      label: 'Verified Only',
      count: stats?.verified_count || 0,
      color: 'success',
      onClick: onVerifiedOnly,
    },
    {
      id: 'live',
      icon: '🔴',
      label: 'Online Now',
      count: stats?.live_count || 0,
      color: 'danger',
      onClick: onLiveOnly,
    },
    {
      id: 'highly_rated',
      icon: '⭐',
      label: 'Popular',
      count: stats?.top_rated_count || 0,
      color: 'warning',
      onClick: onHighlyRated,
    },
  ];

  return (
    <div className="quick-filters">
      {filters.map((filter) => (
        <button
          key={filter.id}
          className={`filter-chip filter-chip--${filter.color} ${isActive(filter.id) ? 'active' : ''}`}
          onClick={filter.onClick}
          aria-pressed={isActive(filter.id)}
        >
          <span className="chip-icon">{filter.icon}</span>
          <span className="chip-label">{filter.label}</span>
          {filter.count > 0 && (
            <span className="chip-count">{filter.count.toLocaleString()}</span>
          )}
        </button>
      ))}
    </div>
  );
}
