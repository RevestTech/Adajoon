import { useState, useEffect, useCallback } from "react";
import { authenticatedFetch } from "../utils/csrf";

export default function AdminDashboard({ onClose }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [overview, setOverview] = useState(null);
  const [userStats, setUserStats] = useState(null);
  const [contentStats, setContentStats] = useState(null);
  const [activityStats, setActivityStats] = useState(null);
  const [analyticsStats, setAnalyticsStats] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [timePeriod, setTimePeriod] = useState(30);

  const loadOverview = useCallback(async () => {
    setLoading(true);
    try {
      const response = await authenticatedFetch("/api/admin/stats/overview");
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setOverview(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadUserStats = useCallback(async () => {
    try {
      const response = await authenticatedFetch(`/api/admin/stats/users?days=${timePeriod}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setUserStats(data);
    } catch (err) {
      setError(err.message);
    }
  }, [timePeriod]);

  const loadContentStats = useCallback(async () => {
    try {
      const response = await authenticatedFetch("/api/admin/stats/content");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setContentStats(data);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const loadActivityStats = useCallback(async () => {
    try {
      const response = await authenticatedFetch(`/api/admin/stats/activity?days=${timePeriod}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setActivityStats(data);
    } catch (err) {
      setError(err.message);
    }
  }, [timePeriod]);

  const loadAnalyticsStats = useCallback(async () => {
    try {
      const [summaryRes, eventsRes, contentRes, authFunnelRes, pathsRes] = await Promise.all([
        authenticatedFetch(`/api/admin/analytics/summary?days=${timePeriod}`),
        authenticatedFetch(`/api/admin/analytics/events-over-time?days=${timePeriod}`),
        authenticatedFetch(`/api/admin/analytics/top-content?days=${timePeriod}&limit=10`),
        authenticatedFetch(`/api/admin/analytics/auth-funnel?days=${timePeriod}`),
        authenticatedFetch(`/api/admin/analytics/paths?days=${timePeriod}&limit=15`),
      ]);

      if (!summaryRes.ok || !eventsRes.ok || !contentRes.ok || !authFunnelRes.ok || !pathsRes.ok) {
        throw new Error('Failed to load analytics');
      }

      const [summary, events, content, authFunnel, paths] = await Promise.all([
        summaryRes.json(),
        eventsRes.json(),
        contentRes.json(),
        authFunnelRes.json(),
        pathsRes.json(),
      ]);

      setAnalyticsStats({ summary, events, content, authFunnel, paths });
    } catch (err) {
      setError(err.message);
    }
  }, [timePeriod]);

  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  useEffect(() => {
    if (activeTab === "users") {
      loadUserStats();
    } else if (activeTab === "content") {
      loadContentStats();
    } else if (activeTab === "activity") {
      loadActivityStats();
    } else if (activeTab === "analytics") {
      loadAnalyticsStats();
    }
  }, [activeTab, timePeriod, loadUserStats, loadContentStats, loadActivityStats, loadAnalyticsStats]);

  if (loading && !overview) {
    return (
      <div className="admin-modal-overlay">
        <div className="admin-modal">
          <div className="admin-loading">Loading admin dashboard...</div>
        </div>
      </div>
    );
  }

  if (error && !overview) {
    return (
      <div className="admin-modal-overlay">
        <div className="admin-modal">
          <div className="admin-error">
            <p>Error loading admin dashboard: {error}</p>
            {error.includes("403") && (
              <p className="admin-error-hint">You do not have admin access.</p>
            )}
            <button onClick={onClose}>Close</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-modal-overlay">
      <div className="admin-modal">
        <div className="admin-header">
          <h1>Admin Dashboard</h1>
          <button className="admin-close" onClick={onClose}>×</button>
        </div>

        <div className="admin-tabs">
          <button
            className={`admin-tab ${activeTab === "overview" ? "active" : ""}`}
            onClick={() => setActiveTab("overview")}
          >
            Overview
          </button>
          <button
            className={`admin-tab ${activeTab === "users" ? "active" : ""}`}
            onClick={() => setActiveTab("users")}
          >
            Users
          </button>
          <button
            className={`admin-tab ${activeTab === "content" ? "active" : ""}`}
            onClick={() => setActiveTab("content")}
          >
            Content
          </button>
          <button
            className={`admin-tab ${activeTab === "activity" ? "active" : ""}`}
            onClick={() => setActiveTab("activity")}
          >
            Activity
          </button>
          <button
            className={`admin-tab ${activeTab === "analytics" ? "active" : ""}`}
            onClick={() => setActiveTab("analytics")}
          >
            Analytics
          </button>
        </div>

        {(activeTab === "users" || activeTab === "activity" || activeTab === "analytics") && (
          <div className="admin-period-selector">
            <label>Time Period:</label>
            <select value={timePeriod} onChange={(e) => setTimePeriod(Number(e.target.value))}>
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
              <option value={365}>Last year</option>
            </select>
          </div>
        )}

        <div className="admin-content">
          {activeTab === "overview" && overview && (
            <div className="admin-overview">
              <div className="admin-section">
                <h2>Users</h2>
                <div className="admin-stats-grid">
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">Total Users</div>
                    <div className="admin-stat-value">{overview.users.total.toLocaleString()}</div>
                  </div>
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">Active This Week</div>
                    <div className="admin-stat-value">{overview.users.active_this_week.toLocaleString()}</div>
                  </div>
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">New This Month</div>
                    <div className="admin-stat-value">{overview.users.new_this_month.toLocaleString()}</div>
                  </div>
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">Paid Users</div>
                    <div className="admin-stat-value">{overview.users.paid_users.toLocaleString()}</div>
                  </div>
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">Admin Users</div>
                    <div className="admin-stat-value">{overview.users.admin_count.toLocaleString()}</div>
                  </div>
                </div>
              </div>

              <div className="admin-section">
                <h2>Content</h2>
                <div className="admin-stats-grid">
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">TV Channels</div>
                    <div className="admin-stat-value">{overview.content.tv_channels.toLocaleString()}</div>
                  </div>
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">Radio Stations</div>
                    <div className="admin-stat-value">{overview.content.radio_stations.toLocaleString()}</div>
                  </div>
                </div>
              </div>

              <div className="admin-section">
                <h2>Activity</h2>
                <div className="admin-stats-grid">
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">Total Favorites</div>
                    <div className="admin-stat-value">{overview.activity.total_favorites.toLocaleString()}</div>
                  </div>
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">Total Votes</div>
                    <div className="admin-stat-value">{overview.activity.total_votes.toLocaleString()}</div>
                  </div>
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">Playlists Created</div>
                    <div className="admin-stat-value">{overview.activity.total_playlists.toLocaleString()}</div>
                  </div>
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">Watches This Week</div>
                    <div className="admin-stat-value">{overview.activity.watches_this_week.toLocaleString()}</div>
                  </div>
                </div>
              </div>

              <div className="admin-section">
                <h2>System Health</h2>
                <div className="admin-health">
                  <div className={`admin-health-item ${overview.system.redis_healthy ? "healthy" : "unhealthy"}`}>
                    <span className="admin-health-icon">{overview.system.redis_healthy ? "✓" : "✗"}</span>
                    <span>Redis: {overview.system.redis_healthy ? "Healthy" : "Unhealthy"}</span>
                  </div>
                  <div className="admin-health-time">
                    Last updated: {new Date(overview.system.timestamp).toLocaleString()}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "users" && userStats && (
            <div className="admin-users">
              <div className="admin-section">
                <h2>Users by Provider</h2>
                <div className="admin-chart-simple">
                  {userStats.users_by_provider.map((item) => (
                    <div key={item.provider} className="admin-chart-bar">
                      <span className="admin-chart-label">{item.provider}</span>
                      <div className="admin-chart-bar-fill" style={{ width: `${(item.count / overview.users.total) * 100}%` }}>
                        <span className="admin-chart-value">{item.count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="admin-section">
                <h2>Users by Subscription Tier</h2>
                <div className="admin-chart-simple">
                  {userStats.users_by_tier.map((item) => (
                    <div key={item.tier} className="admin-chart-bar">
                      <span className="admin-chart-label">{item.tier}</span>
                      <div className="admin-chart-bar-fill" style={{ width: `${(item.count / overview.users.total) * 100}%` }}>
                        <span className="admin-chart-value">{item.count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="admin-section">
                <h2>Most Active Users</h2>
                <div className="admin-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Email</th>
                        <th>Name</th>
                        <th>Joined</th>
                        <th>Favorites</th>
                      </tr>
                    </thead>
                    <tbody>
                      {userStats.most_active_users.map((user, idx) => (
                        <tr key={idx}>
                          <td>{user.email}</td>
                          <td>{user.name || "—"}</td>
                          <td>{user.joined ? new Date(user.joined).toLocaleDateString() : "—"}</td>
                          <td>{user.favorites_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {activeTab === "content" && contentStats && (
            <div className="admin-content-stats">
              <div className="admin-section">
                <h2>Most Favorited TV Channels</h2>
                <div className="admin-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Channel</th>
                        <th>Favorites</th>
                      </tr>
                    </thead>
                    <tbody>
                      {contentStats.most_favorited_tv.map((item, idx) => (
                        <tr key={idx}>
                          <td>
                            {item.logo && <img src={item.logo} alt="" className="admin-table-logo" />}
                            {item.name}
                          </td>
                          <td>{item.favorites}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="admin-section">
                <h2>Most Favorited Radio Stations</h2>
                <div className="admin-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Station</th>
                        <th>Favorites</th>
                      </tr>
                    </thead>
                    <tbody>
                      {contentStats.most_favorited_radio.map((item, idx) => (
                        <tr key={idx}>
                          <td>
                            {item.favicon && <img src={item.favicon} alt="" className="admin-table-logo" />}
                            {item.name}
                          </td>
                          <td>{item.favorites}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="admin-section">
                <h2>Channel Health Status</h2>
                <div className="admin-chart-simple">
                  {contentStats.channels_by_health.map((item) => (
                    <div key={item.status} className="admin-chart-bar">
                      <span className="admin-chart-label">{item.status}</span>
                      <div className="admin-chart-bar-fill" style={{ width: `${(item.count / overview.content.tv_channels) * 100}%` }}>
                        <span className="admin-chart-value">{item.count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="admin-section">
                <h2>Radio Station Health Status</h2>
                <div className="admin-chart-simple">
                  {contentStats.radio_by_health.map((item) => (
                    <div key={item.status} className="admin-chart-bar">
                      <span className="admin-chart-label">{item.status}</span>
                      <div className="admin-chart-bar-fill" style={{ width: `${(item.count / overview.content.radio_stations) * 100}%` }}>
                        <span className="admin-chart-value">{item.count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === "activity" && activityStats && (
            <div className="admin-activity">
              <div className="admin-section">
                <h2>Playlist Activity</h2>
                <div className="admin-stats-grid">
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">Created This Period</div>
                    <div className="admin-stat-value">{activityStats.playlist_activity.created_this_period}</div>
                  </div>
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">Avg Items Per Playlist</div>
                    <div className="admin-stat-value">{activityStats.playlist_activity.avg_items_per_playlist.toFixed(1)}</div>
                  </div>
                </div>
              </div>

              <div className="admin-section">
                <h2>Vote Distribution</h2>
                <div className="admin-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Vote Type</th>
                        <th>Item Type</th>
                        <th>Count</th>
                      </tr>
                    </thead>
                    <tbody>
                      {activityStats.votes_breakdown.map((item, idx) => (
                        <tr key={idx}>
                          <td>{item.vote_type}</td>
                          <td>{item.item_type}</td>
                          <td>{item.count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {activeTab === "analytics" && analyticsStats && (
            <div className="admin-analytics">
              <div className="admin-section">
                <h2>Analytics Summary</h2>
                <div className="admin-stats-grid">
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">Total Events</div>
                    <div className="admin-stat-value">{analyticsStats.summary.total_events.toLocaleString()}</div>
                  </div>
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">Unique Sessions</div>
                    <div className="admin-stat-value">{analyticsStats.summary.unique_sessions.toLocaleString()}</div>
                  </div>
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">Unique Users</div>
                    <div className="admin-stat-value">{analyticsStats.summary.unique_users.toLocaleString()}</div>
                  </div>
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">Avg Session Duration</div>
                    <div className="admin-stat-value">
                      {Math.round(analyticsStats.summary.avg_session_duration_seconds / 60)}m
                    </div>
                  </div>
                </div>
              </div>

              <div className="admin-section">
                <h2>Top Events</h2>
                <div className="admin-chart-simple">
                  {analyticsStats.summary.top_events.map((event) => {
                    const maxCount = analyticsStats.summary.top_events[0]?.count || 1;
                    return (
                      <div key={event.event_name} className="admin-chart-bar">
                        <span className="admin-chart-label">{event.event_name}</span>
                        <div className="admin-chart-bar-fill" style={{ width: `${(event.count / maxCount) * 100}%` }}>
                          <span className="admin-chart-value">{event.count.toLocaleString()}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="admin-section">
                <h2>Events Over Time</h2>
                <div className="admin-chart-simple">
                  {analyticsStats.events.map((day) => {
                    const maxCount = Math.max(...analyticsStats.events.map(d => d.count));
                    return (
                      <div key={day.date} className="admin-chart-bar">
                        <span className="admin-chart-label">{new Date(day.date).toLocaleDateString()}</span>
                        <div className="admin-chart-bar-fill" style={{ width: `${(day.count / maxCount) * 100}%` }}>
                          <span className="admin-chart-value">{day.count.toLocaleString()}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="admin-section">
                <h2>Most Watched Content</h2>
                <div className="admin-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Content</th>
                        <th>Type</th>
                        <th>Plays</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analyticsStats.content.map((item, idx) => (
                        <tr key={idx}>
                          <td>{item.item_name || 'Unknown'}</td>
                          <td>{item.item_type || 'N/A'}</td>
                          <td>{item.play_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="admin-section">
                <h2>Auth Funnel</h2>
                <div className="admin-stats-grid">
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">Attempts</div>
                    <div className="admin-stat-value">{analyticsStats.authFunnel.attempts.toLocaleString()}</div>
                  </div>
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">Successes</div>
                    <div className="admin-stat-value">{analyticsStats.authFunnel.successes.toLocaleString()}</div>
                  </div>
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">Failures</div>
                    <div className="admin-stat-value">{analyticsStats.authFunnel.failures.toLocaleString()}</div>
                  </div>
                  <div className="admin-stat-card">
                    <div className="admin-stat-label">Sessions Lost</div>
                    <div className="admin-stat-value">{analyticsStats.authFunnel.session_lost.toLocaleString()}</div>
                  </div>
                </div>
              </div>

              <div className="admin-section">
                <h2>Auth by Method</h2>
                <div className="admin-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Method</th>
                        <th>Success</th>
                        <th>Failure</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analyticsStats.authFunnel.by_method.map((item) => (
                        <tr key={item.method}>
                          <td>{item.method}</td>
                          <td>{item.success}</td>
                          <td>{item.failure}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="admin-section">
                <h2>Recent Login Failures</h2>
                <div className="admin-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>Method</th>
                        <th>Error</th>
                        <th>Session</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analyticsStats.authFunnel.recent_failures.map((item, idx) => (
                        <tr key={idx}>
                          <td>{item.created_at ? new Date(item.created_at).toLocaleString() : "—"}</td>
                          <td>{item.method}</td>
                          <td>{item.error || "—"}</td>
                          <td>{item.session_id}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="admin-section">
                <h2>Top Screens</h2>
                <div className="admin-chart-simple">
                  {analyticsStats.paths.top_screens.map((item) => {
                    const maxCount = analyticsStats.paths.top_screens[0]?.count || 1;
                    return (
                      <div key={item.screen} className="admin-chart-bar">
                        <span className="admin-chart-label">{item.screen}</span>
                        <div className="admin-chart-bar-fill" style={{ width: `${(item.count / maxCount) * 100}%` }}>
                          <span className="admin-chart-value">{item.count.toLocaleString()}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="admin-section">
                <h2>Top Navigations</h2>
                <div className="admin-table">
                  <table>
                    <thead>
                      <tr>
                        <th>From</th>
                        <th>To</th>
                        <th>Count</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analyticsStats.paths.top_navigations.map((item, idx) => (
                        <tr key={idx}>
                          <td>{item.from_screen}</td>
                          <td>{item.to_screen}</td>
                          <td>{item.count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
