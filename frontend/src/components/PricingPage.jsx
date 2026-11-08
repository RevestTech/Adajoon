import { useState } from "react";
import useSubscription from "../hooks/useSubscription";

function formatPrice(price) {
  if (!price) return "Free";
  return `$${price.toFixed(2)}/mo`;
}

function TierCard({ tierKey, tier, currentTier, isGuest, busyTier, onSubscribe }) {
  const isCurrent = !isGuest && currentTier === tierKey;

  return (
    <div className={`pricing-page-card${isCurrent ? " pricing-page-card--current" : ""}`}>
      {isCurrent && <div className="pricing-page-card-badge">Current plan</div>}
      <h3 className="pricing-page-card-name">{tier.name}</h3>
      <div className="pricing-page-card-price">{formatPrice(tier.price)}</div>
      {tier.features?.length > 0 && (
        <ul className="pricing-page-card-features">
          {tier.features.map((feature) => (
            <li key={feature}>{feature}</li>
          ))}
        </ul>
      )}
      {tier.addons?.length > 0 && (
        <div className="pricing-page-card-addons">
          <div className="pricing-page-card-addons-label">Available add-ons</div>
          <ul className="pricing-page-card-features pricing-page-card-features--addons">
            {tier.addons.map((addon) => (
              <li key={addon.label}>
                {addon.label} <span>+${addon.price.toFixed(2)}/mo</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      <button
        type="button"
        className="pricing-page-card-cta"
        disabled={isCurrent || busyTier === tierKey}
        onClick={() => onSubscribe(tierKey)}
      >
        {isCurrent ? "Current Plan" : busyTier === tierKey ? "Redirecting…" : "Subscribe"}
      </button>
    </div>
  );
}

export default function PricingPage({ isGuest, onLogin, onClose }) {
  const { tiers, tier: currentTier, loading, checkout } = useSubscription();
  const [promoCode, setPromoCode] = useState("");
  const [busyTier, setBusyTier] = useState(null);
  const [error, setError] = useState("");

  const handleSubscribe = async (tierKey) => {
    if (isGuest) {
      onLogin?.();
      return;
    }
    setError("");
    setBusyTier(tierKey);
    try {
      await checkout(tierKey, promoCode.trim() || undefined);
    } catch (err) {
      setError(err.message || "Checkout failed. Please try again.");
    } finally {
      setBusyTier(null);
    }
  };

  const tierEntries = Object.entries(tiers || {});

  return (
    <div className="admin-modal-overlay">
      <div className="admin-modal pricing-page-modal">
        <div className="admin-header">
          <h2>Pricing</h2>
          <button className="admin-close" onClick={onClose} aria-label="Close">×</button>
        </div>
        <div className="admin-content pricing-page-content">
          {loading ? (
            <div className="settings-loading">Loading plans…</div>
          ) : tierEntries.length === 0 ? (
            <p className="pricing-page-empty">Plans are being set up — check back soon.</p>
          ) : (
            <>
              <div className="pricing-page-grid">
                {tierEntries.map(([key, tier]) => (
                  <TierCard
                    key={key}
                    tierKey={key}
                    tier={tier}
                    currentTier={currentTier}
                    isGuest={isGuest}
                    busyTier={busyTier}
                    onSubscribe={handleSubscribe}
                  />
                ))}
              </div>
              <div className="pricing-page-promo">
                <label htmlFor="pricing-promo-code">Have a promo code?</label>
                <input
                  id="pricing-promo-code"
                  type="text"
                  value={promoCode}
                  onChange={(e) => setPromoCode(e.target.value)}
                  placeholder="PROMOCODE"
                />
              </div>
              {error && <p className="pricing-page-error" role="alert">{error}</p>}
              {isGuest && (
                <p className="pricing-page-guest-hint">Sign in to subscribe to a plan.</p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
