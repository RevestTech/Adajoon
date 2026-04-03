/**
 * Hook for managing AirPlay functionality.
 */
import { useState, useEffect } from 'react';
import {
  isAirPlayAvailable,
  enableAirPlay,
  showAirPlayPicker,
  isAirPlaying,
  onAirPlayAvailabilityChange,
  onAirPlayStateChange,
} from '../utils/airplay';

export default function useAirPlay(mediaElementRef) {
  const [available, setAvailable] = useState(false);
  const [deviceAvailable, setDeviceAvailable] = useState(false);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    // Check if AirPlay API is available
    setAvailable(isAirPlayAvailable());
    
    if (!mediaElementRef?.current) return;
    
    const mediaElement = mediaElementRef.current;
    
    // Enable AirPlay on the media element
    enableAirPlay(mediaElement);
    
    // Listen for device availability
    const cleanupAvailability = onAirPlayAvailabilityChange(
      mediaElement,
      setDeviceAvailable
    );
    
    // Listen for AirPlay state changes
    const cleanupState = onAirPlayStateChange(
      mediaElement,
      setPlaying
    );
    
    // Check initial state
    setPlaying(isAirPlaying(mediaElement));
    
    return () => {
      cleanupAvailability();
      cleanupState();
    };
  }, [mediaElementRef]);

  /**
   * Show AirPlay device picker.
   */
  const showPicker = () => {
    if (!mediaElementRef?.current) {
      console.warn('No media element available');
      return false;
    }
    
    return showAirPlayPicker(mediaElementRef.current);
  };

  return {
    available,        // Is AirPlay API available (Safari)?
    deviceAvailable,  // Are AirPlay devices discoverable?
    playing,          // Is currently playing via AirPlay?
    showPicker,       // Function to show device picker
  };
}
