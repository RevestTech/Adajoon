import { useEffect, useRef, useState } from "react";
import {
  fetchAdminUsers,
  fetchSubscriptionTiers,
  makeUserAdmin,
  oneMonthFromNow,
  revokeUserAdmin,
  updateAdminUser,
} from "../api/adminUsers";

export default function UserManager() {
  const [q, setQ] = useState("");
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);
  const [tierOptions, setTierOptions] = useState(["free"]);
  const latestRequest = useRef(0);

  useEffect(() => {
    fetchSubscriptionTiers()
      .then((data) => setTierOptions(["free", ...Object.keys(data.tiers || {})]))
      .catch(() => {});
  }, []);

  const load = (query) => {
    const requestId = ++latestRequest.current;
    setLoading(true);
    setError("");
    fetchAdminUsers({ q: query })
      .then((data) => {
        if (requestId !== latestRequest.current) return;
        setUsers(data.users);
        setTotal(data.total);
      })
      .catch((err) => {
        if (requestId === latestRequest.current) setError(err.message);
      })
      .finally(() => {
        if (requestId === latestRequest.current) setLoading(false);
      });
  };

  useEffect(() => {
    load("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    load(q);
  };

  const runAction = async (userId, action) => {
    setBusyId(userId);
    setError("");
    try {
      await action();
      load(q);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  };

  const handleTierChange = (userId, tier) => {
    runAction(userId, () =>
      updateAdminUser(userId, {
        subscription_tier: tier,
        subscription_status: tier === "free" ? "" : "active",
        subscription_ends_at: tier === "free" ? null : oneMonthFromNow(),
      })
    );
  };

  return (
    <div className="admin-section">
      <h2>Manage Users</h2>
      <form className="pricing-add-feature-row" onSubmit={handleSearch}>
        <input
          className="pricing-input"
          placeholder="Search by email or name"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <button type="submit">Search</button>
      </form>

      {error && <p className="pricing-save-status pricing-save-status--error">{error}</p>}

      {loading ? (
        <p>Loading…</p>
      ) : (
        <div className="admin-table">
          <table>
            <thead>
              <tr>
                <th>Email</th>
                <th>Tier</th>
                <th>Admin</th>
                <th>Parental PIN</th>
                <th>Joined</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.email}</td>
                  <td>
                    <select
                      value={u.subscription_tier || "free"}
                      disabled={busyId === u.id}
                      onChange={(e) => handleTierChange(u.id, e.target.value)}
                    >
                      {tierOptions.map((t) => (
                        <option key={t} value={t}>{t}</option>
                      ))}
                    </select>
                  </td>
                  <td>{u.is_admin ? "Yes" : "No"}</td>
                  <td>{u.has_parental_pin ? "Set" : "—"}</td>
                  <td>{u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}</td>
                  <td className="admin-table-actions">
                    <button
                      type="button"
                      className="admin-table-action-btn"
                      disabled={busyId === u.id}
                      onClick={() =>
                        runAction(u.id, () =>
                          u.is_admin ? revokeUserAdmin(u.id) : makeUserAdmin(u.id)
                        )
                      }
                    >
                      {u.is_admin ? "Revoke Admin" : "Make Admin"}
                    </button>
                    {u.has_parental_pin && (
                      <button
                        type="button"
                        className="admin-table-action-btn"
                        disabled={busyId === u.id}
                        onClick={() =>
                          runAction(u.id, () =>
                            updateAdminUser(u.id, { clear_parental_pin: true })
                          )
                        }
                      >
                        Clear PIN
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={6}>No users found.</td>
                </tr>
              )}
            </tbody>
          </table>
          {total > users.length && (
            <p className="settings-section-hint">
              Showing {users.length} of {total} - refine your search to narrow further.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
