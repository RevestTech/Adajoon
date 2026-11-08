/**
 * A/B testing and feature flags (stub implementation).
 * PostHog removed in favor of custom analytics.
 */

export function initializeExperiments() {
}

export function identifyUser(userId, properties = {}) {
}

export function resetUser() {
}

export function getFeatureFlag(flagKey, defaultValue = false) {
  return defaultValue;
}

export function isFeatureEnabled(flagKey) {
  return false;
}

export function getExperimentVariant(experimentKey, defaultVariant = 'control') {
  return defaultVariant;
}

export function trackExperimentExposure(experimentKey, variant) {
}

export function reloadFeatureFlags() {
  return Promise.resolve();
}

export function trackExperimentEvent(eventName, properties = {}) {
}

export function getUserProperties() {
  return {};
}

export function isExperimentsAvailable() {
  return false;
}
