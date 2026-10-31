import { useEffect, useState } from "react";
import { fetchAdminRevenue, fetchAdminSubscriptions, updateAdminUser } from "../api/adminUsers";

const TIER_OPTIONS = ["free", "plus", "pro", "family"];

export default function SubscriptionManager() {
  const [subs, setSubs] = useState([]);
  const [revenue, setRevenue] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  const load = () => {
    setLoading(true);
    setError("");
    Promise.all([fetchAdminSubscriptions(), fetchAdminRevenue()])
      .then(([subsData, revenueData]) => {
        setSubs(subsData);
        setRevenue(revenueData);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleComp = async (userId, tier) => {
    setBusyId(userId);
    setError("");
    try {
      await updateAdminUser(userId, {
        subscription_tier: tier,
        subscription_status: tier === "free" ? "" : "active",
      });
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="admin-section">
      <h2>Subscriptions</h2>
      <p className="settings-section-hint">
        Stripe stays the source of truth for real billing - use this to comp a
        free month or manually fix an account, and the Stripe dashboard for
        anything involving an actual charge or refund.
      </p>

      {revenue && (
        <div className="admin-stats-grid">
          <div className="admin-stat-card">
            <div className="admin-stat-label">Estimated MRR</div>
            <div className="admin-stat-value">${revenue.mrr.toFixed(2)}</div>
          </div>
          {revenue.breakdown.map((b) => (
            <div className="admin-stat-card" key={b.tier}>
              <div className="admin-stat-label">{b.tier}</div>
              <div className="admin-stat-value">
                {b.subscribers} · ${b.mrr.toFixed(2)}
              </div>
            </div>
          ))}
        </div>
      )}

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
                <th>Status</th>
                <th>Ends</th>
                <th>Stripe</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {subs.map((s) => (
                <tr key={s.id}>
                  <td>{s.email}</td>
                  <td>{s.tier}</td>
                  <td>{s.status || "—"}</td>
                  <td>{s.ends_at ? new Date(s.ends_at).toLocaleDateString() : "—"}</td>
                  <td>
                    {s.stripe_customer_id ? (
                      <a
                        href={`https://dashboard.stripe.com/customers/${s.stripe_customer_id}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Open
                      </a>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>
                    <select
                      disabled={busyId === s.id}
                      value={s.tier}
                      onChange={(e) => handleComp(s.id, e.target.value)}
                    >
                      {TIER_OPTIONS.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
              {subs.length === 0 && (
                <tr>
                  <td colSpan={6}>No subscribers yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
