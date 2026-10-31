import { useState } from "react";
import {
  searchAdminChannels,
  searchAdminRadio,
  setChannelHidden,
  setRadioHidden,
} from "../api/adminContent";

function ModerationTable({ kind, results, busyId, onToggle }) {
  if (results.length === 0) return null;
  return (
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Country</th>
          <th>Health</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {results.map((r) => (
          <tr key={r.id}>
            <td>{r.name}</td>
            <td>{r.country_code || "—"}</td>
            <td>{r.health_status}</td>
            <td>
              <button
                type="button"
                className="admin-table-action-btn"
                disabled={busyId === r.id}
                onClick={() => onToggle(kind, r.id, !r.admin_hidden)}
              >
                {r.admin_hidden ? "Unhide" : "Hide"}
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function ContentModeration() {
  const [channelQuery, setChannelQuery] = useState("");
  const [channels, setChannels] = useState([]);
  const [radioQuery, setRadioQuery] = useState("");
  const [stations, setStations] = useState([]);
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState("");

  const searchChannels = async (e) => {
    e.preventDefault();
    if (!channelQuery.trim()) return;
    try {
      setChannels(await searchAdminChannels(channelQuery.trim()));
    } catch (err) {
      setError(err.message);
    }
  };

  const searchStations = async (e) => {
    e.preventDefault();
    if (!radioQuery.trim()) return;
    try {
      setStations(await searchAdminRadio(radioQuery.trim()));
    } catch (err) {
      setError(err.message);
    }
  };

  const handleToggle = async (kind, id, hidden) => {
    setBusyId(id);
    setError("");
    try {
      if (kind === "channel") {
        await setChannelHidden(id, hidden);
        setChannels((prev) =>
          prev.map((c) => (c.id === id ? { ...c, admin_hidden: hidden } : c))
        );
      } else {
        await setRadioHidden(id, hidden);
        setStations((prev) =>
          prev.map((s) => (s.id === id ? { ...s, admin_hidden: hidden } : s))
        );
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="admin-section">
      <h2>Hide a Channel or Station</h2>
      <p className="settings-section-hint">
        A manual hide sticks across the sync job (the automated sync overwrites
        its own activity/health flags every run, but never this).
      </p>

      {error && <p className="pricing-save-status pricing-save-status--error">{error}</p>}

      <form className="pricing-add-feature-row" onSubmit={searchChannels}>
        <input
          className="pricing-input"
          placeholder="Search TV channels by name"
          value={channelQuery}
          onChange={(e) => setChannelQuery(e.target.value)}
        />
        <button type="submit">Search</button>
      </form>
      <div className="admin-table">
        <ModerationTable
          kind="channel"
          results={channels}
          busyId={busyId}
          onToggle={handleToggle}
        />
      </div>

      <form className="pricing-add-feature-row" onSubmit={searchStations}>
        <input
          className="pricing-input"
          placeholder="Search radio stations by name"
          value={radioQuery}
          onChange={(e) => setRadioQuery(e.target.value)}
        />
        <button type="submit">Search</button>
      </form>
      <div className="admin-table">
        <ModerationTable
          kind="station"
          results={stations}
          busyId={busyId}
          onToggle={handleToggle}
        />
      </div>
    </div>
  );
}
