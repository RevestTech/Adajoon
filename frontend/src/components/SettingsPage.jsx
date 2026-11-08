import { useCallback, useEffect, useState } from "react";
import useParentalControls from "../hooks/useParentalControls";
import { clearWatchHistory, deleteWatchHistoryItem, fetchWatchHistory } from "../api/history";
import { fetchChannel } from "../api/channels";
import { fetchStation } from "../api/radio";

function formatWatchedAt(isoString) {
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function ParentalControlsTab() {
  const { kidsModeEnabled, hasPin, loading, setPin, toggleKidsMode, removePin } =
    useParentalControls();
  const [pinInput, setPinInput] = useState("");
  const [removeInput, setRemoveInput] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const handleSetPin = async (e) => {
    e.preventDefault();
    setMessage("");
    setBusy(true);
    try {
      await setPin(pinInput);
      setPinInput("");
      setMessage("PIN saved.");
    } catch (err) {
      setMessage(err.message || "Failed to save PIN");
    } finally {
      setBusy(false);
    }
  };

  const handleRemovePin = async (e) => {
    e.preventDefault();
    setMessage("");
    setBusy(true);
    try {
      const ok = await removePin(removeInput);
      setRemoveInput("");
      setMessage(ok ? "PIN removed." : "Could not remove PIN — check it and try again.");
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <div className="settings-loading">Loading…</div>;

  return (
    <div className="settings-section">
      <h3 className="settings-section-title">Kids Mode</h3>
      <p className="settings-section-hint">
        Restrict mature content and require a PIN to switch back to the full catalog.
      </p>
      <label className="settings-toggle-row">
        <span>Kids mode</span>
        <input
          type="checkbox"
          checked={kidsModeEnabled}
          disabled={busy || (!kidsModeEnabled && !hasPin)}
          onChange={(e) => toggleKidsMode(e.target.checked)}
        />
      </label>
      {!hasPin && (
        <p className="settings-section-hint settings-section-hint--warn">
          Set a PIN below before enabling kids mode, so you can turn it back off.
        </p>
      )}

      <h3 className="settings-section-title">Parental PIN</h3>
      <form className="settings-form" onSubmit={handleSetPin}>
        <input
          type="password"
          inputMode="numeric"
          pattern="[0-9]*"
          minLength={4}
          maxLength={6}
          placeholder={hasPin ? "New 4-6 digit PIN" : "Set a 4-6 digit PIN"}
          value={pinInput}
          onChange={(e) => setPinInput(e.target.value)}
          className="settings-input"
        />
        <button type="submit" className="settings-btn" disabled={busy || pinInput.length < 4}>
          {hasPin ? "Update PIN" : "Set PIN"}
        </button>
      </form>

      {hasPin && (
        <form className="settings-form" onSubmit={handleRemovePin}>
          <input
            type="password"
            inputMode="numeric"
            pattern="[0-9]*"
            minLength={4}
            maxLength={6}
            placeholder="Enter PIN to remove it"
            value={removeInput}
            onChange={(e) => setRemoveInput(e.target.value)}
            className="settings-input"
          />
          <button type="submit" className="settings-btn settings-btn--danger" disabled={busy || removeInput.length < 4}>
            Remove PIN
          </button>
        </form>
      )}

      {message && <p className="settings-message">{message}</p>}
    </div>
  );
}

function WatchHistoryTab({ onSelectChannel, onSelectStation }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchWatchHistory({ limit: 100 });
      setItems(data || []);
      setError("");
    } catch (err) {
      setError(err.message || "Failed to load watch history");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleDelete = async (id) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
    try {
      await deleteWatchHistoryItem(id);
    } catch {
      load();
    }
  };

  const handleClear = async () => {
    setItems([]);
    try {
      await clearWatchHistory();
    } catch {
      load();
    }
  };

  const [resolving, setResolving] = useState(false);

  const handleSelect = async (item) => {
    setResolving(true);
    try {
      if (item.item_type === "tv") {
        const channel = await fetchChannel(item.item_id);
        onSelectChannel?.(channel);
      } else {
        const station = await fetchStation(item.item_id);
        onSelectStation?.(station);
      }
    } catch {
      // Stream may no longer exist; leave the list as-is.
    } finally {
      setResolving(false);
    }
  };

  if (loading) return <div className="settings-loading">Loading…</div>;
  if (error) return <div className="settings-error">{error}</div>;

  return (
    <div className="settings-section">
      <div className="settings-section-header-row">
        <h3 className="settings-section-title">Watch History</h3>
        {items.length > 0 && (
          <button type="button" className="settings-btn settings-btn--danger" onClick={handleClear}>
            Clear All
          </button>
        )}
      </div>
      {items.length === 0 ? (
        <p className="settings-section-hint">Nothing watched yet.</p>
      ) : (
        <ul className="settings-history-list">
          {items.map((item) => (
            <li key={item.id} className="settings-history-item">
              <button
                type="button"
                className="settings-history-item-main"
                onClick={() => handleSelect(item)}
                disabled={resolving}
                aria-busy={resolving}
              >
                {item.item_logo ? (
                  <img src={item.item_logo} alt="" className="settings-history-item-logo" />
                ) : (
                  <span className="settings-history-item-logo settings-history-item-logo--placeholder" />
                )}
                <span className="settings-history-item-info">
                  <span className="settings-history-item-name">{item.item_name}</span>
                  <span className="settings-history-item-meta">
                    {item.item_type === "tv" ? "TV" : "Radio"} · {formatWatchedAt(item.watched_at)}
                  </span>
                </span>
              </button>
              <button
                type="button"
                className="settings-history-item-remove"
                aria-label={`Remove ${item.item_name} from history`}
                onClick={() => handleDelete(item.id)}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function SettingsPage({ onClose, onSelectChannel, onSelectStation }) {
  const [activeTab, setActiveTab] = useState("history");

  return (
    <div className="admin-modal-overlay">
      <div className="admin-modal">
        <div className="admin-header">
          <h2>Settings</h2>
          <button className="admin-close" onClick={onClose}>×</button>
        </div>

        <div className="admin-tabs">
          <button
            className={`admin-tab ${activeTab === "history" ? "active" : ""}`}
            onClick={() => setActiveTab("history")}
          >
            Watch History
          </button>
          <button
            className={`admin-tab ${activeTab === "parental" ? "active" : ""}`}
            onClick={() => setActiveTab("parental")}
          >
            Parental Controls
          </button>
        </div>

        <div className="admin-content">
          {activeTab === "history" && (
            <WatchHistoryTab onSelectChannel={onSelectChannel} onSelectStation={onSelectStation} />
          )}
          {activeTab === "parental" && <ParentalControlsTab />}
        </div>
      </div>
    </div>
  );
}
