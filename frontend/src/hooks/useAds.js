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
import useSubscription from './useSubscription';

export default function useAds(videoElementRef, adContainerRef) {
  const [adPlaying, setAdPlaying] = useState(false);
  const [adsEnabled, setAdsEnabled] = useState(false);

  const { user } = useAuth();
  const { adsEnabled: adsEnabledGlobally, adsSettingResolved } = useSubscription();

  const adsLoaderRef = useRef(null);
  const adsManagerRef = useRef(null);
  const adDisplayContainerRef = useRef(null);
  // Mirrors `adsEnabled` synchronously so playPreRoll() - which may be called
  // from a closure captured before this effect last ran - always reads the
  // current value instead of whatever `adsEnabled` was at the time its own
  // closure was created.
  const adsEnabledRef = useRef(false);
  // True once the IMA loader for the current mount is actually ready to
  // accept a requestAds() call - lets playPreRoll() wait out the brief
  // window between mount and loader creation instead of silently losing
  // the very first ad request.
  const adsLoaderReadyRef = useRef(false);
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
    // Don't flip ads on (or off) until the admin's real ads_enabled setting
    // has actually resolved - otherwise a fast player mount could enable
    // ads under the optimistic default and then immediately disable them
    // once the real value loads.
    if (!adsSettingResolved) return;

    const shouldEnable = areAdsSupported() && shouldShowAds(user, adsEnabledGlobally);
    adsEnabledRef.current = shouldEnable;
    setAdsEnabled(shouldEnable);

    if (!shouldEnable) return;

    const videoElement = videoElementRef?.current;
    const adContainer = adContainerRef?.current;

    if (!videoElement || !adContainer) return;

    adDisplayContainerRef.current = createAdDisplayContainer(videoElement, adContainer);

    const adsLoader = createAdsLoader(adDisplayContainerRef.current, videoElement);
    if (!adsLoader) return;

    adsLoaderRef.current = adsLoader;
    adsLoaderReadyRef.current = true;

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
      adsLoaderReadyRef.current = false;
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
  }, [videoElementRef, adContainerRef, user, adsEnabledGlobally, adsSettingResolved, finishPreRoll]);

  /**
   * Request and play a pre-roll ad before content. Resolves once the ad
   * sequence completes, is skipped, errors, or 10s pass with no response -
   * never resolves early just because the ads manager finished loading.
   *
   * If ads are enabled but the IMA loader hasn't finished initializing yet
   * (the player can call this before the effect above finishes), waits up
   * to LOADER_READY_TIMEOUT_MS rather than silently dropping the call.
   */
  const playPreRoll = useCallback(async () => {
    if (!adsEnabledRef.current) {
      return Promise.resolve();
    }

    if (!adsLoaderReadyRef.current) {
      const LOADER_READY_TIMEOUT_MS = 2000;
      const POLL_INTERVAL_MS = 50;
      const deadline = Date.now() + LOADER_READY_TIMEOUT_MS;
      while (!adsLoaderReadyRef.current && Date.now() < deadline) {
        await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
      }
    }

    if (!adsLoaderRef.current || !adDisplayContainerRef.current) {
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
  }, [videoElementRef, finishPreRoll]);

  return {
    adsEnabled,
    adPlaying,
    playPreRoll,
  };
}
