import { useState, useCallback } from 'react';
import { analytics } from '../analytics';

export function useShare() {
  const [shareSupported] = useState(() => {
    return typeof navigator !== 'undefined' && 'share' in navigator;
  });

  const shareContent = useCallback(async ({ title, text, url }) => {
    // Try Web Share API first (mobile)
    if (shareSupported) {
      try {
        await navigator.share({ title, text, url });
        return { success: true, method: 'native' };
      } catch (error) {
        if (error.name === 'AbortError') {
          return { success: false, error: 'Share cancelled' };
        }
        console.warn('Web Share API failed, falling back to clipboard:', error);
      }
    }

    // Fallback to clipboard
    try {
      await navigator.clipboard.writeText(url);
      return { success: true, method: 'clipboard' };
    } catch (error) {
      console.error('Clipboard write failed:', error);
      return { success: false, error: 'Failed to copy link' };
    }
  }, [shareSupported]);

  const shareTvChannel = useCallback(async (channel) => {
    const url = `${window.location.origin}/tv/channel/${channel.id}`;
    const result = await shareContent({
      title: `Watch ${channel.name} on Adajoon`,
      text: `Check out ${channel.name} - live streaming on Adajoon`,
      url,
    });
    
    if (result.success) {
      analytics.trackShare(result.method, 'tv', channel);
    }
    
    return result;
  }, [shareContent]);

  const shareRadioStation = useCallback(async (station) => {
    const url = `${window.location.origin}/radio/station/${station.id}`;
    const result = await shareContent({
      title: `Listen to ${station.name} on Adajoon`,
      text: `Check out ${station.name} - streaming on Adajoon`,
      url,
    });
    
    if (result.success) {
      analytics.trackShare(result.method, 'radio', station);
    }
    
    return result;
  }, [shareContent]);

  return {
    shareSupported,
    shareContent,
    shareTvChannel,
    shareRadioStation,
  };
}
