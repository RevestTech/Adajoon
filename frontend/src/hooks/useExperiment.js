/**
 * Hook for A/B testing and feature flags.
 */
import { useState, useEffect } from 'react';
import {
  getExperimentVariant,
  getFeatureFlag,
  isFeatureEnabled,
  trackExperimentExposure,
  reloadFeatureFlags,
  isExperimentsAvailable,
} from '../experiments';

/**
 * Hook to get experiment variant and track exposure.
 * @param {string} experimentKey - Experiment key from PostHog
 * @param {string} defaultVariant - Default variant (usually 'control')
 */
export function useExperiment(experimentKey, defaultVariant = 'control') {
  const [variant, setVariant] = useState(defaultVariant);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isExperimentsAvailable()) {
      setLoading(false);
      return;
    }

    // Get variant
    const loadedVariant = getExperimentVariant(experimentKey, defaultVariant);
    setVariant(loadedVariant);
    
    // Track exposure
    trackExperimentExposure(experimentKey, loadedVariant);
    
    setLoading(false);
  }, [experimentKey, defaultVariant]);

  return { variant, loading };
}

/**
 * Hook to get feature flag value.
 * @param {string} flagKey - Feature flag key
 * @param {*} defaultValue - Default value
 */
export function useFeatureFlag(flagKey, defaultValue = false) {
  const [value, setValue] = useState(defaultValue);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isExperimentsAvailable()) {
      setLoading(false);
      return;
    }

    const flagValue = getFeatureFlag(flagKey, defaultValue);
    setValue(flagValue);
    setLoading(false);
  }, [flagKey, defaultValue]);

  return { value, loading };
}

/**
 * Hook to check if a feature is enabled (boolean flags).
 * @param {string} flagKey - Feature flag key
 */
export function useFeatureEnabled(flagKey) {
  const [enabled, setEnabled] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isExperimentsAvailable()) {
      setLoading(false);
      return;
    }

    const isEnabled = isFeatureEnabled(flagKey);
    setEnabled(isEnabled);
    setLoading(false);
  }, [flagKey]);

  return { enabled, loading };
}
