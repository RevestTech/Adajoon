import { useEffect, useRef } from 'react';
import { analytics } from '../analytics';

/**
 * Hook to track playback duration with periodic heartbeats.
 * Emits events every 30 seconds while content is playing.
 */
export function usePlaybackTracking(isPlaying, itemType, item) {
  const startTimeRef = useRef(null);
  const lastHeartbeatRef = useRef(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!item || !isPlaying) {
      // Stop tracking when paused or no item
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      
      // Send final heartbeat if we were tracking
      if (startTimeRef.current && lastHeartbeatRef.current) {
        const totalDuration = Math.floor((Date.now() - startTimeRef.current) / 1000);
        analytics.track('Playback Ended', {
          item_type: itemType,
          item_id: item.id,
          item_name: item.name,
          duration_seconds: totalDuration,
        });
      }
      
      startTimeRef.current = null;
      lastHeartbeatRef.current = null;
      return;
    }

    // Start tracking
    if (!startTimeRef.current) {
      startTimeRef.current = Date.now();
      lastHeartbeatRef.current = Date.now();
      
      analytics.track('Playback Started', {
        item_type: itemType,
        item_id: item.id,
        item_name: item.name,
        item_country: item.country,
        item_category: item.categories || item.tags,
      });
    }

    // Setup heartbeat interval (every 30 seconds)
    intervalRef.current = setInterval(() => {
      const now = Date.now();
      const sessionDuration = Math.floor((now - startTimeRef.current) / 1000);
      const sinceLast = Math.floor((now - lastHeartbeatRef.current) / 1000);
      
      analytics.track('Playback Heartbeat', {
        item_type: itemType,
        item_id: item.id,
        item_name: item.name,
        session_duration_seconds: sessionDuration,
        heartbeat_interval_seconds: sinceLast,
      });
      
      lastHeartbeatRef.current = now;
    }, 30000); // 30 seconds

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isPlaying, itemType, item]);

  // Track on unmount (user navigates away)
  useEffect(() => {
    return () => {
      if (startTimeRef.current && item) {
        const totalDuration = Math.floor((Date.now() - startTimeRef.current) / 1000);
        
        // Only send if watched for at least 5 seconds
        if (totalDuration >= 5) {
          analytics.track('Playback Session', {
            item_type: itemType,
            item_id: item.id,
            item_name: item.name,
            total_duration_seconds: totalDuration,
          });
        }
      }
    };
  }, [item, itemType]);

  return null;
}
