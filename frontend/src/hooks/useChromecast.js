/**
 * Hook for managing Chromecast functionality.
 */
import { useState, useEffect, useRef } from 'react';
import {
  initializeCast,
  isCastAvailable,
  getCastSession,
  castMedia,
  stopCasting,
  isCasting,
} from '../utils/chromecast';

export default function useChromecast() {
  const [available, setAvailable] = useState(false);
  const [casting, setCasting] = useState(false);
  const [error, setError] = useState(null);
  const contextRef = useRef(null);

  useEffect(() => {
    // Initialize Cast SDK
    initializeCast().then((context) => {
      if (context) {
        contextRef.current = context;
        setAvailable(true);

        // Listen for session state changes
        context.addEventListener(
          cast.framework.CastContextEventType.SESSION_STATE_CHANGED,
          (event) => {
            const isActive = event.sessionState === cast.framework.SessionState.SESSION_STARTED;
            setCasting(isActive);
          }
        );
      }
    }).catch((err) => {
      console.error('Failed to initialize Cast:', err);
      setError(err.message);
    });
  }, []);

  /**
   * Cast a channel or station to Chromecast.
   */
  const cast = async (item) => {
    if (!available) {
      setError('Chromecast not available');
      return false;
    }

    try {
      await castMedia({
        url: item.stream_url || item.url,
        title: item.name,
        subtitle: item.country || '',
        logo: item.logo || item.favicon,
        type: item.type || 'tv',
      });
      setCasting(true);
      return true;
    } catch (err) {
      setError(err.message);
      console.error('Cast failed:', err);
      return false;
    }
  };

  /**
   * Stop current cast session.
   */
  const stop = () => {
    try {
      stopCasting();
      setCasting(false);
    } catch (err) {
      console.error('Failed to stop cast:', err);
    }
  };

  return {
    available,
    casting,
    error,
    cast,
    stop,
  };
}
