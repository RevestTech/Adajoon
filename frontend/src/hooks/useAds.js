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
  const [adsLoaded, setAdsLoaded] = useState(false);
  const [adPlaying, setAdPlaying] = useState(false);
  const [adsEnabled, setAdsEnabled] = useState(false);
  
  const { user } = useAuth();
  
  const adsLoaderRef = useRef(null);
  const adsManagerRef = useRef(null);
  const adDisplayContainerRef = useRef(null);

  useEffect(() => {
    // Check if ads should be enabled
    const shouldEnable = areAdsSupported() && shouldShowAds(user);
    setAdsEnabled(shouldEnable);
    
    if (!shouldEnable) return;
    
    // Initialize IMA
    const videoElement = videoElementRef?.current;
    const adContainer = adContainerRef?.current;
    
    if (!videoElement || !adContainer) return;
    
    // Create ad display container
    adDisplayContainerRef.current = createAdDisplayContainer(videoElement, adContainer);
    
    // Create ads loader
    const adsLoader = createAdsLoader(adDisplayContainerRef.current, videoElement);
    if (!adsLoader) return;
    
    adsLoaderRef.current = adsLoader;
    
    // Listen for ads loaded
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
          onAdComplete: () => {
            setAdPlaying(false);
          },
          onAdSkipped: () => {
            setAdPlaying(false);
          },
          onAllAdsComplete: () => {
            setAdPlaying(false);
            setAdsLoaded(true);
            videoElement.play(); // Resume main content
          },
          onAdError: (adErrorEvent) => {
            console.error('Ad error:', adErrorEvent.getError());
            setAdPlaying(false);
            setAdsLoaded(true);
            adsManager.destroy();
            videoElement.play(); // Play content even if ad fails
          },
        });
        
        setAdsLoaded(true);
      },
      false
    );
    
    // Listen for ad errors
    adsLoader.addEventListener(
      google.ima.AdErrorEvent.Type.AD_ERROR,
      (adErrorEvent) => {
        console.error('Ad loading error:', adErrorEvent.getError());
        setAdsLoaded(true);
        videoElement.play(); // Play content even if ad loading fails
      },
      false
    );
    
    // Cleanup
    return () => {
      if (adsManagerRef.current) {
        adsManagerRef.current.destroy();
      }
      if (adsLoaderRef.current) {
        adsLoaderRef.current.destroy();
      }
    };
  }, [videoElementRef, adContainerRef, user]);

  /**
   * Play pre-roll ad before content.
   */
  const playPreRoll = useCallback(() => {
    if (!adsEnabled || !adsLoaderRef.current || !adDisplayContainerRef.current) {
      return Promise.resolve(); // Skip ads if not enabled
    }
    
    return new Promise((resolve) => {
      // Initialize ad display container
      adDisplayContainerRef.current.initialize();
      
      // Request ads
      const videoElement = videoElementRef?.current;
      if (videoElement) {
        const width = videoElement.offsetWidth || 640;
        const height = videoElement.offsetHeight || 360;
        requestAds(adsLoaderRef.current, adDisplayContainerRef.current, width, height);
      }
      
      // Resolve when ads complete or error
      const checkComplete = setInterval(() => {
        if (adsLoaded && !adPlaying) {
          clearInterval(checkComplete);
          resolve();
        }
      }, 100);
      
      // Timeout after 10 seconds
      setTimeout(() => {
        clearInterval(checkComplete);
        resolve();
      }, 10000);
    });
  }, [adsEnabled, adsLoaded, adPlaying, videoElementRef]);

  /**
   * Start ads manager (call after playPreRoll).
   */
  const startAds = useCallback(() => {
    if (!adsManagerRef.current) return;
    
    try {
      const videoElement = videoElementRef?.current;
      if (videoElement) {
        const width = videoElement.offsetWidth || 640;
        const height = videoElement.offsetHeight || 360;
        adsManagerRef.current.init(width, height, google.ima.ViewMode.NORMAL);
        adsManagerRef.current.start();
      }
    } catch (error) {
      console.error('Failed to start ads:', error);
    }
  }, [videoElementRef]);

  return {
    adsEnabled,
    adsLoaded,
    adPlaying,
    playPreRoll,
    startAds,
  };
}
