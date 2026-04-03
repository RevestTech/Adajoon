/**
 * A/B testing and feature flags with PostHog.
 */
import posthog from 'posthog-js';

// Initialize PostHog
const POSTHOG_KEY = import.meta.env.VITE_POSTHOG_KEY;
const POSTHOG_HOST = import.meta.env.VITE_POSTHOG_HOST || 'https://app.posthog.com';

let initialized = false;

/**
 * Initialize PostHog (call once on app startup).
 */
export function initializeExperiments() {
  if (initialized || !POSTHOG_KEY) {
    return;
  }
  
  posthog.init(POSTHOG_KEY, {
    api_host: POSTHOG_HOST,
    autocapture: false,  // We handle tracking manually
    capture_pageview: false,  // Manual page tracking
    capture_pageleave: true,
    loaded: (ph) => {
      if (import.meta.env.DEV) {
        console.log('PostHog initialized');
      }
    },
  });
  
  initialized = true;
}

/**
 * Identify user for experiments (call after login).
 */
export function identifyUser(userId, properties = {}) {
  if (!initialized) return;
  
  posthog.identify(userId.toString(), properties);
}

/**
 * Reset user identity (call on logout).
 */
export function resetUser() {
  if (!initialized) return;
  
  posthog.reset();
}

/**
 * Get feature flag value.
 * @param {string} flagKey - Feature flag key
 * @param {*} defaultValue - Default value if flag not found
 */
export function getFeatureFlag(flagKey, defaultValue = false) {
  if (!initialized) return defaultValue;
  
  return posthog.getFeatureFlag(flagKey) ?? defaultValue;
}

/**
 * Check if feature flag is enabled.
 * @param {string} flagKey - Feature flag key
 */
export function isFeatureEnabled(flagKey) {
  if (!initialized) return false;
  
  return posthog.isFeatureEnabled(flagKey);
}

/**
 * Get experiment variant.
 * @param {string} experimentKey - Experiment key
 * @param {string} defaultVariant - Default variant
 */
export function getExperimentVariant(experimentKey, defaultVariant = 'control') {
  if (!initialized) return defaultVariant;
  
  const variant = posthog.getFeatureFlag(experimentKey);
  return variant || defaultVariant;
}

/**
 * Track experiment exposure (call when user sees variant).
 */
export function trackExperimentExposure(experimentKey, variant) {
  if (!initialized) return;
  
  posthog.capture('$experiment_exposure', {
    experiment: experimentKey,
    variant,
  });
}

/**
 * Reload feature flags from server.
 */
export function reloadFeatureFlags() {
  if (!initialized) return Promise.resolve();
  
  return new Promise((resolve) => {
    posthog.reloadFeatureFlags(() => {
      resolve();
    });
  });
}

/**
 * Track custom event for experiment metrics.
 */
export function trackExperimentEvent(eventName, properties = {}) {
  if (!initialized) return;
  
  posthog.capture(eventName, properties);
}

/**
 * Get current user properties (for debugging).
 */
export function getUserProperties() {
  if (!initialized) return {};
  
  return posthog.get_property('$set') || {};
}

/**
 * Check if PostHog is initialized.
 */
export function isExperimentsAvailable() {
  return initialized;
}
