import { useState, useEffect, useCallback, useRef } from "react";
import {
  fetchAdminTiers,
  createAdminTier,
  updateAdminTier,
  deleteAdminTier,
  createAdminFeature,
  updateAdminFeature,
  deleteAdminFeature,
  fetchAdminDiscounts,
  createAdminDiscount,
  updateAdminDiscount,
  deleteAdminDiscount,
  fetchAdminPricingSettings,
  updateAdminPricingSettings,
} from "../api/adminPricing";

const centsToDollars = (cents) => (cents == null ? "" : (cents / 100).toFixed(2));
const dollarsToCents = (dollars) => Math.round(Number(dollars || 0) * 100);

function TierRow({ tier, onChange, onDelete, onAddFeature, onUpdateFeature, onDeleteFeature }) {
  const [name, setName] = useState(tier.name);
  const [price, setPrice] = useState(centsToDollars(tier.monthly_price_cents));
  const [newFeatureLabel, setNewFeatureLabel] = useState("");
  const [newFeatureIsAddon, setNewFeatureIsAddon] = useState(false);
  const [newFeaturePrice, setNewFeaturePrice] = useState("");
  // idle | saving | saved | error - cleared back to idle a couple seconds
  // after a save, so an edit always gives some visible confirmation.
  const [saveStatus, setSaveStatus] = useState("idle");
  const saveSeqRef = useRef(0);
  const resetTimeoutRef = useRef(null);

  const save = async () => {
    const seq = ++saveSeqRef.current;
    if (resetTimeoutRef.current) clearTimeout(resetTimeoutRef.current);
    setSaveStatus("saving");
    try {
      await onChange(tier.id, { name, monthly_price_cents: dollarsToCents(price) });
      if (seq !== saveSeqRef.current) return; // a newer save has started since
      setSaveStatus("saved");
    } catch {
      if (seq !== saveSeqRef.current) return;
      setSaveStatus("error");
    } finally {
      if (seq === saveSeqRef.current) {
        resetTimeoutRef.current = setTimeout(() => setSaveStatus("idle"), 2000);
      }
    }
  };

  useEffect(() => {
    return () => {
      if (resetTimeoutRef.current) clearTimeout(resetTimeoutRef.current);
    };
  }, []);

  const addFeature = () => {
    if (!newFeatureLabel.trim()) return;
    onAddFeature(tier.id, {
      key: newFeatureLabel.trim().toLowerCase().replace(/[^a-z0-9]+/g, "_"),
      label: newFeatureLabel.trim(),
      is_addon: newFeatureIsAddon,
      addon_price_cents: newFeatureIsAddon ? dollarsToCents(newFeaturePrice) : 0,
    });
    setNewFeatureLabel("");
    setNewFeaturePrice("");
    setNewFeatureIsAddon(false);
  };

  return (
    <div className="admin-section pricing-tier-card">
      <div className="pricing-tier-row">
        <input
          className="pricing-input pricing-input-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onBlur={save}
          aria-label="Tier name"
        />
        <span className="pricing-tier-key">{tier.key}</span>
        <div className="pricing-price-field">
          <span>$</span>
          <input
            className="pricing-input pricing-input-price"
            type="number"
            step="0.01"
            min="0"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            onBlur={save}
            aria-label="Monthly price"
          />
          <span>/mo</span>
        </div>
        <label className="pricing-toggle">
          <input
            type="checkbox"
            checked={tier.is_active}
            onChange={(e) => onChange(tier.id, { is_active: e.target.checked }).catch(() => {})}
          />
          Active
        </label>
        <span
          role="status"
          aria-live="polite"
          className={`pricing-save-status pricing-save-status--${saveStatus}`}
        >
          {saveStatus === "saving"
            ? "Saving…"
            : saveStatus === "saved"
              ? "Saved"
              : saveStatus === "error"
                ? "Failed to save"
                : ""}
        </span>
        <button
          type="button"
          className="admin-table-action-btn admin-table-action-danger"
          onClick={() => onDelete(tier.id)}
        >
          Delete tier
        </button>
      </div>

      <ul className="pricing-feature-list">
        {tier.features.map((f) => (
          <li key={f.id} className="pricing-feature-item">
            <span>{f.label}</span>
            {f.is_addon && (
              <span className="pricing-feature-addon-price">
                +${centsToDollars(f.addon_price_cents)}
              </span>
            )}
            <button
              type="button"
              className="pricing-feature-toggle"
              onClick={() => onUpdateFeature(f.id, { is_active: !f.is_active })}
              title={f.is_active ? "Deactivate" : "Activate"}
            >
              {f.is_active ? "Active" : "Inactive"}
            </button>
            <button
              type="button"
              className="pricing-feature-remove"
              onClick={() => onDeleteFeature(f.id)}
              aria-label={`Remove ${f.label}`}
            >
              ×
            </button>
          </li>
        ))}
      </ul>

      <div className="pricing-add-feature-row">
        <input
          className="pricing-input"
          placeholder="New feature label"
          value={newFeatureLabel}
          onChange={(e) => setNewFeatureLabel(e.target.value)}
        />
        <label className="pricing-toggle">
          <input
            type="checkbox"
            checked={newFeatureIsAddon}
            onChange={(e) => setNewFeatureIsAddon(e.target.checked)}
          />
          Paid add-on
        </label>
        {newFeatureIsAddon && (
          <div className="pricing-price-field">
            <span>$</span>
            <input
              className="pricing-input pricing-input-price"
              type="number"
              step="0.01"
              min="0"
              value={newFeaturePrice}
              onChange={(e) => setNewFeaturePrice(e.target.value)}
            />
          </div>
        )}
        <button type="button" className="admin-table-action-btn" onClick={addFeature}>
          Add feature
        </button>
      </div>
    </div>
  );
}

function PricingPreview({ tiers, onClose }) {
  const modalRef = useRef(null);
  const closeButtonRef = useRef(null);

  useEffect(() => {
    const previouslyFocused = document.activeElement;
    closeButtonRef.current?.focus();

    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key !== "Tab") return;
      const focusable = modalRef.current?.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (!focusable || focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      previouslyFocused?.focus?.();
    };
  }, [onClose]);

  const visibleTiers = [...tiers]
    .filter((t) => t.is_active)
    .sort((a, b) => a.sort_order - b.sort_order);

  return (
    <div className="pricing-preview-overlay" onClick={onClose}>
      <div
        className="pricing-preview-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="pricing-preview-title"
        ref={modalRef}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="pricing-preview-header">
          <h2 id="pricing-preview-title">What customers will see</h2>
          <button type="button" className="admin-table-action-btn" onClick={onClose} ref={closeButtonRef}>
            Close preview
          </button>
        </div>
        <p className="admin-section-hint">
          Inactive tiers are hidden here too, same as on the real pricing page.
        </p>
        <div className="pricing-preview-cards">
          {visibleTiers.map((tier) => {
            const included = tier.features.filter((f) => f.is_active && !f.is_addon);
            const addons = tier.features.filter((f) => f.is_active && f.is_addon);
            return (
              <div key={tier.id} className="pricing-preview-card">
                <div className="pricing-preview-card-name">{tier.name}</div>
                <div className="pricing-preview-card-price">
                  ${centsToDollars(tier.monthly_price_cents)}
                  <span className="pricing-preview-card-period">/mo</span>
                </div>
                <ul className="pricing-preview-feature-list">
                  {included.map((f) => (
                    <li key={f.id}>{f.label}</li>
                  ))}
                </ul>
                {addons.length > 0 && (
                  <>
                    <div className="pricing-preview-addons-label">Available add-ons</div>
                    <ul className="pricing-preview-feature-list pricing-preview-feature-list--addons">
                      {addons.map((f) => (
                        <li key={f.id}>
                          {f.label} <span>+${centsToDollars(f.addon_price_cents)}/mo</span>
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function DiscountForm({ tiers, onCreate }) {
  const [code, setCode] = useState("");
  const [percentOff, setPercentOff] = useState("");
  const [tierId, setTierId] = useState("");

  const submit = (e) => {
    e.preventDefault();
    if (!code.trim() || !percentOff) return;
    onCreate({
      code: code.trim(),
      percent_off: Number(percentOff),
      tier_id: tierId ? Number(tierId) : null,
    });
    setCode("");
    setPercentOff("");
    setTierId("");
  };

  return (
    <form className="pricing-add-feature-row" onSubmit={submit}>
      <input
        className="pricing-input"
        placeholder="CODE"
        value={code}
        onChange={(e) => setCode(e.target.value.toUpperCase())}
      />
      <div className="pricing-price-field">
        <input
          className="pricing-input pricing-input-price"
          type="number"
          min="1"
          max="100"
          placeholder="%"
          value={percentOff}
          onChange={(e) => setPercentOff(e.target.value)}
        />
        <span>% off</span>
      </div>
      <select value={tierId} onChange={(e) => setTierId(e.target.value)}>
        <option value="">All tiers</option>
        {tiers.map((t) => (
          <option key={t.id} value={t.id}>
            {t.name}
          </option>
        ))}
      </select>
      <button type="submit" className="admin-table-action-btn">
        Create discount
      </button>
    </form>
  );
}

export default function PricingManager() {
  const [tiers, setTiers] = useState([]);
  const [discounts, setDiscounts] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [newTierKey, setNewTierKey] = useState("");
  const [newTierName, setNewTierName] = useState("");
  const [previewOpen, setPreviewOpen] = useState(false);
  const [adsEnabled, setAdsEnabled] = useState(true);
  const [adsSaving, setAdsSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [tiersData, discountsData, settingsData] = await Promise.all([
        fetchAdminTiers(),
        fetchAdminDiscounts(),
        fetchAdminPricingSettings(),
      ]);
      setTiers(tiersData);
      setDiscounts(discountsData);
      setAdsEnabled(settingsData.ads_enabled);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleAdsToggle = async () => {
    const next = !adsEnabled;
    setAdsSaving(true);
    try {
      const result = await updateAdminPricingSettings({ ads_enabled: next });
      setAdsEnabled(result.ads_enabled);
    } catch (err) {
      setError(err.message);
    } finally {
      setAdsSaving(false);
    }
  };

  const handleTierChange = async (id, patch) => {
    try {
      const updated = await updateAdminTier(id, patch);
      setTiers((prev) => prev.map((t) => (t.id === id ? { ...t, ...updated } : t)));
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const handleTierDelete = async (id) => {
    if (!window.confirm("Delete this tier? This cannot be undone.")) return;
    try {
      await deleteAdminTier(id);
      setTiers((prev) => prev.filter((t) => t.id !== id));
    } catch (err) {
      setError(err.message);
    }
  };

  const handleAddTier = async (e) => {
    e.preventDefault();
    if (!newTierKey.trim() || !newTierName.trim()) return;
    try {
      const created = await createAdminTier({
        key: newTierKey.trim().toLowerCase().replace(/[^a-z0-9]+/g, "_"),
        name: newTierName.trim(),
        sort_order: tiers.length,
      });
      setTiers((prev) => [...prev, { ...created, features: [] }]);
      setNewTierKey("");
      setNewTierName("");
    } catch (err) {
      setError(err.message);
    }
  };

  const handleAddFeature = async (tierId, data) => {
    try {
      const created = await createAdminFeature({ ...data, tier_id: tierId });
      setTiers((prev) =>
        prev.map((t) => (t.id === tierId ? { ...t, features: [...t.features, created] } : t))
      );
    } catch (err) {
      setError(err.message);
    }
  };

  const handleUpdateFeature = async (featureId, patch) => {
    try {
      const updated = await updateAdminFeature(featureId, patch);
      setTiers((prev) =>
        prev.map((t) => ({
          ...t,
          features: t.features.map((f) => (f.id === featureId ? updated : f)),
        }))
      );
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteFeature = async (featureId) => {
    try {
      await deleteAdminFeature(featureId);
      setTiers((prev) =>
        prev.map((t) => ({ ...t, features: t.features.filter((f) => f.id !== featureId) }))
      );
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCreateDiscount = async (data) => {
    try {
      const created = await createAdminDiscount(data);
      setDiscounts((prev) => [created, ...prev]);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleToggleDiscount = async (id, is_active) => {
    try {
      const updated = await updateAdminDiscount(id, { is_active });
      setDiscounts((prev) => prev.map((d) => (d.id === id ? updated : d)));
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteDiscount = async (id) => {
    try {
      await deleteAdminDiscount(id);
      setDiscounts((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <div className="admin-loading">Loading pricing…</div>;

  return (
    <div className="pricing-manager">
      {error && <div className="admin-error">{error}</div>}

      {previewOpen && <PricingPreview tiers={tiers} onClose={() => setPreviewOpen(false)} />}

      <div className="admin-section">
        <div className="pricing-section-header">
          <h2>Monetization</h2>
        </div>
        <label className="pricing-toggle">
          <input
            type="checkbox"
            checked={adsEnabled}
            disabled={adsSaving}
            onChange={handleAdsToggle}
          />
          Show ads to free/guest users
        </label>
        <p className="settings-section-hint">
          Global kill switch - turn this off to stop all pre-roll ads immediately
          (e.g. an ad vendor issue), independent of per-tier eligibility below.
        </p>
      </div>

      <div className="admin-section">
        <div className="pricing-section-header">
          <h2>Tiers</h2>
          <button type="button" className="admin-table-action-btn" onClick={() => setPreviewOpen(true)}>
            Preview pricing page
          </button>
        </div>
        <p className="admin-section-hint">
          Edit name, monthly price, and per-tier features. Checkout and the public pricing
          display read from this list.
        </p>
        {tiers.map((tier) => (
          <TierRow
            key={tier.id}
            tier={tier}
            onChange={handleTierChange}
            onDelete={handleTierDelete}
            onAddFeature={handleAddFeature}
            onUpdateFeature={handleUpdateFeature}
            onDeleteFeature={handleDeleteFeature}
          />
        ))}
        <form className="pricing-add-feature-row" onSubmit={handleAddTier}>
          <input
            className="pricing-input"
            placeholder="key (e.g. premium_plus)"
            value={newTierKey}
            onChange={(e) => setNewTierKey(e.target.value)}
          />
          <input
            className="pricing-input"
            placeholder="Display name"
            value={newTierName}
            onChange={(e) => setNewTierName(e.target.value)}
          />
          <button type="submit" className="admin-table-action-btn">
            Add tier
          </button>
        </form>
      </div>

      <div className="admin-section">
        <h2>Discount codes</h2>
        <p className="admin-section-hint">
          Codes customers can enter at checkout. Restrict to one tier, or leave open to all.
        </p>
        <ul className="pricing-discount-list">
          {discounts.map((d) => (
            <li key={d.id} className="pricing-discount-item">
              <span className="pricing-discount-code">{d.code}</span>
              <span>
                {d.percent_off ? `${d.percent_off}% off` : `$${centsToDollars(d.amount_off_cents)} off`}
              </span>
              <span className="pricing-discount-scope">
                {d.tier_id ? tiers.find((t) => t.id === d.tier_id)?.name || "tier" : "all tiers"}
              </span>
              <span className="pricing-discount-usage">
                {d.redemption_count} used{d.max_redemptions ? ` / ${d.max_redemptions}` : ""}
              </span>
              <button
                type="button"
                className="pricing-feature-toggle"
                onClick={() => handleToggleDiscount(d.id, !d.is_active)}
              >
                {d.is_active ? "Active" : "Disabled"}
              </button>
              <button
                type="button"
                className="pricing-feature-remove"
                onClick={() => handleDeleteDiscount(d.id)}
                aria-label={`Delete ${d.code}`}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
        <DiscountForm tiers={tiers} onCreate={handleCreateDiscount} />
      </div>
    </div>
  );
}
