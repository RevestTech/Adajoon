/**
 * Hook for managing video/audio ads with Google IMA SDK.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import {
  createAdDisplayContainer,
  createAdsLoader,
  requestAds,
  setupAdsManager,
  areAdsSupported,
  shouldShowAds,
} from '../utils/ads';
import { useAuth } from './useAuth';

export default function useAds(videoElementRef, adContainerRef) {
  const [adPlaying, setAdPlaying] = useState(false);
  const [adsEnabled, setAdsEnabled] = useState(false);

  const { user } = useAuth();

  const adsLoaderRef = useRef(null);
  const adsManagerRef = useRef(null);
  const adDisplayContainerRef = useRef(null);
  // Resolves the in-flight playPreRoll() promise once the ad sequence
  // genuinely finishes (completed, skipped, or errored) - set per call so
  // we never resolve early just because the manager loaded.
  const resolvePreRollRef = useRef(null);

  const finishPreRoll = useCallback(() => {
    setAdPlaying(false);
    const resolve = resolvePreRollRef.current;
    resolvePreRollRef.current = null;
    resolve?.();
  }, []);

  useEffect(() => {
    const shouldEnable = areAdsSupported() && shouldShowAds(user);
    setAdsEnabled(shouldEnable);

    if (!shouldEnable) return;

    const videoElement = videoElementRef?.current;
    const adContainer = adContainerRef?.current;

    if (!videoElement || !adContainer) return;

    adDisplayContainerRef.current = createAdDisplayContainer(videoElement, adContainer);

    const adsLoader = createAdsLoader(adDisplayContainerRef.current, videoElement);
    if (!adsLoader) return;

    adsLoaderRef.current = adsLoader;

    adsLoader.addEventListener(
      google.ima.AdsManagerLoadedEvent.Type.ADS_MANAGER_LOADED,
      (event) => {
        const adsManager = event.getAdsManager(videoElement);
        adsManagerRef.current = adsManager;

        setupAdsManager(adsManager, {
          onAdStarted: () => {
            setAdPlaying(true);
            videoElement.pause(); // Pause main content during ad
          },
          onAdComplete: finishPreRoll,
          onAdSkipped: finishPreRoll,
          onAllAdsComplete: finishPreRoll,
          onAdError: (adErrorEvent) => {
            console.error('Ad error:', adErrorEvent.getError());
            adsManager.destroy();
            finishPreRoll();
          },
        });

        try {
          const width = videoElement.offsetWidth || 640;
          const height = videoElement.offsetHeight || 360;
          adsManager.init(width, height, google.ima.ViewMode.NORMAL);
          adsManager.start();
        } catch (error) {
          console.error('Failed to start ads:', error);
          finishPreRoll();
        }
      },
      false
    );

    adsLoader.addEventListener(
      google.ima.AdErrorEvent.Type.AD_ERROR,
      (adErrorEvent) => {
        console.error('Ad loading error:', adErrorEvent.getError());
        finishPreRoll();
      },
      false
    );

    return () => {
      if (adsManagerRef.current) {
        adsManagerRef.current.destroy();
        adsManagerRef.current = null;
      }
      if (adsLoaderRef.current) {
        adsLoaderRef.current.destroy();
        adsLoaderRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [videoElementRef, adContainerRef, user, finishPreRoll]);

  /**
   * Request and play a pre-roll ad before content. Resolves once the ad
   * sequence completes, is skipped, errors, or 10s pass with no response -
   * never resolves early just because the ads manager finished loading.
   */
  const playPreRoll = useCallback(() => {
    if (!adsEnabled || !adsLoaderRef.current || !adDisplayContainerRef.current) {
      return Promise.resolve();
    }

    return new Promise((resolve) => {
      resolvePreRollRef.current = resolve;

      adDisplayContainerRef.current.initialize();

      const videoElement = videoElementRef?.current;
      if (videoElement) {
        const width = videoElement.offsetWidth || 640;
        const height = videoElement.offsetHeight || 360;
        requestAds(adsLoaderRef.current, adDisplayContainerRef.current, width, height);
      }

      setTimeout(() => {
        if (resolvePreRollRef.current === resolve) {
          finishPreRoll();
        }
      }, 10000);
    });
  }, [adsEnabled, videoElementRef, finishPreRoll]);

  return {
    adsEnabled,
    adPlaying,
    playPreRoll,
  };
}
