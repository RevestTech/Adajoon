import { useEffect, useRef, useState } from "react";
import { fetchAuditLog } from "../api/adminAuditLog";

const PAGE_SIZE = 50;

export default function AuditLogViewer() {
  const [entries, setEntries] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const latestRequest = useRef(0);

  useEffect(() => {
    const requestId = ++latestRequest.current;
    setLoading(true);
    setError("");
    fetchAuditLog(PAGE_SIZE, offset)
      .then((data) => {
        if (requestId !== latestRequest.current) return;
        setEntries(data.entries);
        setTotal(data.total);
      })
      .catch((err) => {
        if (requestId === latestRequest.current) setError(err.message);
      })
      .finally(() => {
        if (requestId === latestRequest.current) setLoading(false);
      });
  }, [offset]);

  return (
    <div className="admin-section">
      <h2>Audit Log</h2>
      <p className="settings-section-hint">
        Admin actions that changed state - who did what, when. Read-only.
      </p>

      {error && <p className="pricing-save-status pricing-save-status--error">{error}</p>}

      {loading ? (
        <p>Loading…</p>
      ) : (
        <>
          <div className="admin-table">
            <table>
              <thead>
                <tr>
                  <th>When</th>
                  <th>Admin</th>
                  <th>Action</th>
                  <th>Target</th>
                  <th>Detail</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((e) => (
                  <tr key={e.id}>
                    <td>{e.created_at ? new Date(e.created_at).toLocaleString() : ""}</td>
                    <td>{e.admin_email}</td>
                    <td>{e.action}</td>
                    <td>
                      {e.target_type ? `${e.target_type}:${e.target_id ?? ""}` : "—"}
                    </td>
                    <td>{e.detail || "—"}</td>
                  </tr>
                ))}
                {entries.length === 0 && (
                  <tr>
                    <td colSpan={5}>No admin actions logged yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginTop: "0.75rem" }}>
            <button
              className="admin-table-action-btn"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            >
              Newer
            </button>
            <span>
              {total === 0 ? 0 : offset + 1}-{Math.min(offset + PAGE_SIZE, total)} of {total}
            </span>
            <button
              className="admin-table-action-btn"
              disabled={offset + PAGE_SIZE >= total}
              onClick={() => setOffset(offset + PAGE_SIZE)}
            >
              Older
            </button>
          </div>
        </>
      )}
    </div>
  );
}
