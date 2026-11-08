import { useEffect, useRef } from 'react';
import { analytics } from '../analytics';

/**
 * Hook to track overall user session duration and engagement.
 * Tracks time on site, active time, idle time, and pages visited.
 */
export function useSessionTracking() {
  const sessionStartRef = useRef(null);
  const lastActivityRef = useRef(null);
  const isActiveRef = useRef(true);
  const activityTimeRef = useRef(0);
  const idleTimeRef = useRef(0);
  const pagesVisitedRef = useRef(0);
  const heartbeatIntervalRef = useRef(null);
  const idleTimeoutRef = useRef(null);

  useEffect(() => {
    // Reset accumulators on every mount so a remount (route change, React
    // Strict Mode double-invoke) starts a fresh session instead of adding
    // on top of a previous mount's totals.
    sessionStartRef.current = Date.now();
    lastActivityRef.current = Date.now();
    isActiveRef.current = true;
    activityTimeRef.current = 0;
    idleTimeRef.current = 0;
    pagesVisitedRef.current = 1;

    analytics.track('Session Started', {
      timestamp: new Date().toISOString(),
      user_agent: navigator.userAgent,
      screen_width: window.screen.width,
      screen_height: window.screen.height,
    });

    // Track activity (mouse, keyboard, touch, scroll)
    const handleActivity = () => {
      const now = Date.now();
      
      if (!isActiveRef.current) {
        // User became active again
        isActiveRef.current = true;
        const idleDuration = Math.floor((now - lastActivityRef.current) / 1000);
        idleTimeRef.current += idleDuration;
        
        analytics.track('User Became Active', {
          idle_duration_seconds: idleDuration,
        });
      }
      
      lastActivityRef.current = now;

      // Reset idle timeout
      if (idleTimeoutRef.current) {
        clearTimeout(idleTimeoutRef.current);
      }
      
      // Mark as idle after 60 seconds of no activity
      idleTimeoutRef.current = setTimeout(() => {
        if (isActiveRef.current) {
          isActiveRef.current = false;
          analytics.track('User Became Idle', {
            active_duration_seconds: Math.floor((Date.now() - lastActivityRef.current) / 1000),
          });
        }
      }, 60000); // 60 seconds
    };

    // Session heartbeat every 60 seconds
    const sendHeartbeat = () => {
      const now = Date.now();
      const totalDuration = Math.floor((now - sessionStartRef.current) / 1000);
      
      if (isActiveRef.current) {
        const activeSince = Math.floor((now - lastActivityRef.current) / 1000);
        activityTimeRef.current += activeSince;
      }

      analytics.track('Session Heartbeat', {
        total_duration_seconds: totalDuration,
        active_time_seconds: activityTimeRef.current,
        idle_time_seconds: idleTimeRef.current,
        pages_visited: pagesVisitedRef.current,
        is_active: isActiveRef.current,
      });
    };

    heartbeatIntervalRef.current = setInterval(sendHeartbeat, 60000); // 1 minute

    // Attach event listeners
    const events = ['mousedown', 'keydown', 'touchstart', 'scroll', 'mousemove'];
    events.forEach(event => {
      window.addEventListener(event, handleActivity, { passive: true });
    });

    // Track visibility changes (tab switches)
    const handleVisibilityChange = () => {
      if (document.hidden) {
        analytics.track('Tab Hidden', {
          time_since_start: Math.floor((Date.now() - sessionStartRef.current) / 1000),
        });
      } else {
        analytics.track('Tab Visible', {
          time_since_start: Math.floor((Date.now() - sessionStartRef.current) / 1000),
        });
        pagesVisitedRef.current += 1;
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Send final session summary on unmount/close
    const handleUnload = () => {
      const now = Date.now();
      const totalDuration = Math.floor((now - sessionStartRef.current) / 1000);
      
      if (isActiveRef.current) {
        activityTimeRef.current += Math.floor((now - lastActivityRef.current) / 1000);
      } else {
        idleTimeRef.current += Math.floor((now - lastActivityRef.current) / 1000);
      }

      analytics.track('Session Ended', {
        total_duration_seconds: totalDuration,
        active_time_seconds: activityTimeRef.current,
        idle_time_seconds: idleTimeRef.current,
        pages_visited: pagesVisitedRef.current,
        engagement_rate: totalDuration > 0 ? (activityTimeRef.current / totalDuration * 100).toFixed(2) : 0,
      });
    };

    window.addEventListener('beforeunload', handleUnload);

    return () => {
      // Cleanup
      events.forEach(event => {
        window.removeEventListener(event, handleActivity);
      });
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('beforeunload', handleUnload);
      
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }
      
      if (idleTimeoutRef.current) {
        clearTimeout(idleTimeoutRef.current);
      }

      // Send final session summary
      handleUnload();
    };
  }, []);

  return null;
}
