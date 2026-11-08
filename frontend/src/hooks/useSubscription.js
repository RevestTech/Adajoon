/**
 * Hook for managing user subscriptions.
 */
import { useState, useEffect } from 'react';
import { authenticatedFetch } from '../utils/csrf';

export default function useSubscription() {
  const [tier, setTier] = useState('free');
  const [status, setStatus] = useState('');
  const [endsAt, setEndsAt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tiers, setTiers] = useState({});
  // Starts closed (false) rather than optimistically open - until the real
  // admin setting is known, we'd rather under-show ads than show them to a
  // user the admin just turned them off for.
  const [adsEnabled, setAdsEnabled] = useState(false);
  const [adsSettingResolved, setAdsSettingResolved] = useState(false);

  /**
   * Load available tiers (and the global ads on/off switch, which rides
   * along on this same response rather than a separate endpoint).
   */
  const loadTiers = async () => {
    try {
      const response = await fetch(`/api/subscriptions/tiers`);
      if (response.ok) {
        const data = await response.json();
        setTiers(data.tiers || {});
        setAdsEnabled(data.ads_enabled !== false);
      }
    } catch (error) {
      console.error('Failed to load tiers:', error);
    } finally {
      setAdsSettingResolved(true);
    }
  };

  /**
   * Load subscription status.
   */
  const loadStatus = async () => {
    setLoading(true);
    
    try {
      const response = await authenticatedFetch(`/api/subscriptions/status`);
      if (response.ok) {
        const data = await response.json();
        setTier(data.tier || 'free');
        setStatus(data.status || '');
        setEndsAt(data.ends_at);
      }
    } catch (error) {
      console.error('Failed to load subscription status:', error);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Create checkout session and redirect to Stripe.
   */
  const checkout = async (targetTier, promoCode) => {
    try {
      const successUrl = `${window.location.origin}/subscription/success`;
      const cancelUrl = `${window.location.origin}/subscription/cancel`;

      const response = await authenticatedFetch(`/api/subscriptions/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tier: targetTier,
          success_url: successUrl,
          cancel_url: cancelUrl,
          ...(promoCode ? { promo_code: promoCode } : {}),
        }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Checkout failed');
      }
      
      const data = await response.json();
      
      // Redirect to Stripe checkout
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
      
      return true;
    } catch (error) {
      console.error('Checkout failed:', error);
      throw error;
    }
  };

  /**
   * Open Stripe customer portal for managing subscription.
   */
  const openPortal = async () => {
    try {
      const returnUrl = window.location.origin;
      
      const response = await authenticatedFetch(`/api/subscriptions/portal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ return_url: returnUrl }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to create portal session');
      }
      
      const data = await response.json();
      
      // Redirect to portal
      if (data.portal_url) {
        window.location.href = data.portal_url;
      }
      
      return true;
    } catch (error) {
      console.error('Portal access failed:', error);
      throw error;
    }
  };

  /**
   * Check if user has premium access. A comped tier with an expiry in the
   * past no longer counts, even if status is still "active" - the admin
   * grant endpoint sets an end date rather than flipping status back itself.
   */
  const isPremium = () => {
    if (tier === 'free' || status !== 'active') return false;
    if (endsAt && new Date(endsAt) < new Date()) return false;
    return true;
  };

  /**
   * Check if user can access a specific feature.
   */
  const hasFeature = (feature) => {
    const tierInfo = tiers[tier];
    if (!tierInfo) return false;
    
    return tierInfo.features?.includes(feature) || false;
  };

  // Load on mount
  useEffect(() => {
    loadTiers();
    loadStatus();
  }, []);

  return {
    tier,
    status,
    endsAt,
    loading,
    tiers,
    adsEnabled,
    adsSettingResolved,
    checkout,
    openPortal,
    isPremium,
    hasFeature,
    reload: loadStatus,
  };
}
