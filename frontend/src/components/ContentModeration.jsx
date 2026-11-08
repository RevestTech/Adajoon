import { useRef, useState } from "react";
import {
  searchAdminChannels,
  searchAdminRadio,
  setChannelHidden,
  setRadioHidden,
} from "../api/adminContent";

function ModerationTable({ kind, results, busyIds, onToggle }) {
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
                disabled={busyIds.has(r.id)}
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

const EMPTY_BUSY = new Set();

export default function ContentModeration() {
  const [channelQuery, setChannelQuery] = useState("");
  const [channels, setChannels] = useState([]);
  const [channelPage, setChannelPage] = useState(1);
  const [channelLoading, setChannelLoading] = useState(false);
  const [channelError, setChannelError] = useState("");
  const channelRequest = useRef(0);

  const [radioQuery, setRadioQuery] = useState("");
  const [stations, setStations] = useState([]);
  const [radioPage, setRadioPage] = useState(1);
  const [radioLoading, setRadioLoading] = useState(false);
  const [radioError, setRadioError] = useState("");
  const radioRequest = useRef(0);

  // Toggle (hide/unhide) busy state is tracked per-id across both tables so
  // a channel toggle in flight can never be mistaken for a station toggle.
  const [busyIds, setBusyIds] = useState(EMPTY_BUSY);

  const runChannelSearch = (query, page) => {
    const requestId = ++channelRequest.current;
    setChannelLoading(true);
    setChannelError("");
    searchAdminChannels(query, page)
      .then((results) => {
        if (requestId !== channelRequest.current) return;
        setChannels((prev) => (page === 1 ? results : [...prev, ...results]));
        setChannelPage(page);
      })
      .catch((err) => {
        if (requestId === channelRequest.current) {
          setChannelError(err.message);
          if (page === 1) setChannels([]);
        }
      })
      .finally(() => {
        if (requestId === channelRequest.current) setChannelLoading(false);
      });
  };

  const runRadioSearch = (query, page) => {
    const requestId = ++radioRequest.current;
    setRadioLoading(true);
    setRadioError("");
    searchAdminRadio(query, page)
      .then((results) => {
        if (requestId !== radioRequest.current) return;
        setStations((prev) => (page === 1 ? results : [...prev, ...results]));
        setRadioPage(page);
      })
      .catch((err) => {
        if (requestId === radioRequest.current) {
          setRadioError(err.message);
          if (page === 1) setStations([]);
        }
      })
      .finally(() => {
        if (requestId === radioRequest.current) setRadioLoading(false);
      });
  };

  const searchChannels = (e) => {
    e.preventDefault();
    if (!channelQuery.trim()) return;
    runChannelSearch(channelQuery.trim(), 1);
  };

  const searchStations = (e) => {
    e.preventDefault();
    if (!radioQuery.trim()) return;
    runRadioSearch(radioQuery.trim(), 1);
  };

  const handleToggle = async (kind, id, hidden) => {
    setBusyIds((prev) => new Set(prev).add(id));
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
      if (kind === "channel") setChannelError(err.message);
      else setRadioError(err.message);
    } finally {
      setBusyIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  return (
    <div className="admin-section">
      <h2>Hide a Channel or Station</h2>
      <p className="settings-section-hint">
        A manual hide sticks across the sync job (the automated sync overwrites
        its own activity/health flags every run, but never this).
      </p>

      <form className="pricing-add-feature-row" onSubmit={searchChannels}>
        <input
          className="pricing-input"
          placeholder="Search TV channels by name"
          value={channelQuery}
          onChange={(e) => setChannelQuery(e.target.value)}
        />
        <button type="submit" disabled={channelLoading}>
          {channelLoading ? "Searching…" : "Search"}
        </button>
      </form>
      {channelError && (
        <p className="pricing-save-status pricing-save-status--error">{channelError}</p>
      )}
      <div className="admin-table">
        <ModerationTable
          kind="channel"
          results={channels}
          busyIds={busyIds}
          onToggle={handleToggle}
        />
        {channels.length > 0 && (
          <button
            type="button"
            className="admin-table-action-btn"
            disabled={channelLoading}
            onClick={() => runChannelSearch(channelQuery.trim(), channelPage + 1)}
          >
            Load more
          </button>
        )}
      </div>

      <form className="pricing-add-feature-row" onSubmit={searchStations}>
        <input
          className="pricing-input"
          placeholder="Search radio stations by name"
          value={radioQuery}
          onChange={(e) => setRadioQuery(e.target.value)}
        />
        <button type="submit" disabled={radioLoading}>
          {radioLoading ? "Searching…" : "Search"}
        </button>
      </form>
      {radioError && (
        <p className="pricing-save-status pricing-save-status--error">{radioError}</p>
      )}
      <div className="admin-table">
        <ModerationTable
          kind="station"
          results={stations}
          busyIds={busyIds}
          onToggle={handleToggle}
        />
        {stations.length > 0 && (
          <button
            type="button"
            className="admin-table-action-btn"
            disabled={radioLoading}
            onClick={() => runRadioSearch(radioQuery.trim(), radioPage + 1)}
          >
            Load more
          </button>
        )}
      </div>
    </div>
  );
}
