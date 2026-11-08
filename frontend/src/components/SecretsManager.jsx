import { useEffect, useRef, useState } from "react";
import { clearAdminSecret, fetchAdminSecrets, setAdminSecret } from "../api/adminSecrets";

const SOURCE_LABEL = {
  vault: "Set in vault",
  env: "Set via env var",
  unconfigured: "Not set",
  error: "Vault unreachable",
  sealed: "Vault sealed - try again shortly",
};

function SecretRow({ secret, onSave, onClear }) {
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [savedAt, setSavedAt] = useState(0);

  const save = async (e) => {
    e.preventDefault();
    if (!value.trim()) return;
    if (
      secret.sensitive &&
      !window.confirm(`Overwrite ${secret.label}? This takes effect after the next restart.`)
    ) {
      return;
    }
    setBusy(true);
    setError("");
    try {
      await onSave(secret.key, value.trim());
      setValue("");
      setSavedAt(Date.now());
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const clear = async () => {
    if (!window.confirm(`Clear ${secret.label} from the vault?`)) return;
    setBusy(true);
    setError("");
    try {
      await onClear(secret.key);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="admin-secret-row">
      <div className="admin-secret-row__info">
        <span className="admin-secret-row__label">
          {secret.label}
          {secret.sensitive && <span className="admin-secret-row__tag">Sensitive</span>}
        </span>
        <span className="admin-secret-row__description">{secret.description}</span>
        <span className={`admin-secret-row__status admin-secret-row__status--${secret.source}`}>
          {SOURCE_LABEL[secret.source] || secret.source}
        </span>
      </div>
      <form className="admin-secret-row__form" onSubmit={save}>
        <input
          type="password"
          className="pricing-input"
          placeholder="New value…"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={busy}
          autoComplete="off"
        />
        <button type="submit" className="admin-table-action-btn" disabled={busy || !value.trim()}>
          {busy ? "Saving…" : "Save"}
        </button>
        {secret.source === "vault" && (
          <button
            type="button"
            className="admin-table-action-btn admin-table-action-danger"
            onClick={clear}
            disabled={busy}
          >
            Clear
          </button>
        )}
      </form>
      {error && <p className="pricing-save-status pricing-save-status--error">{error}</p>}
      {!error && savedAt > 0 && (
        <p className="pricing-save-status pricing-save-status--saved">
          Saved - restart the backend for it to take effect.
        </p>
      )}
    </div>
  );
}

export default function SecretsManager() {
  const [secrets, setSecrets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const latestRequest = useRef(0);

  const load = () => {
    const requestId = ++latestRequest.current;
    setLoading(true);
    setError("");
    fetchAdminSecrets()
      .then((data) => {
        if (requestId === latestRequest.current) setSecrets(data);
      })
      .catch((err) => {
        if (requestId === latestRequest.current) setError(err.message);
      })
      .finally(() => {
        if (requestId === latestRequest.current) setLoading(false);
      });
  };

  useEffect(load, []);

  const handleSave = async (key, value) => {
    await setAdminSecret(key, value);
    load();
  };

  const handleClear = async (key) => {
    await clearAdminSecret(key);
    load();
  };

  return (
    <div className="admin-section">
      <h2>Secrets</h2>
      <p className="settings-section-hint">
        Writes directly into the shared vault (adajoon:&lt;key&gt;) - never
        shown once saved, only whether it's configured. The running backend
        reads these once at startup, so a new or changed value needs a
        restart/redeploy to take effect.
      </p>

      {error && <p className="pricing-save-status pricing-save-status--error">{error}</p>}

      {loading ? (
        <p>Loading…</p>
      ) : (
        <div className="admin-secrets-list">
          {secrets.map((secret) => (
            <SecretRow
              key={secret.key}
              secret={secret}
              onSave={handleSave}
              onClear={handleClear}
            />
          ))}
        </div>
      )}
    </div>
  );
}
