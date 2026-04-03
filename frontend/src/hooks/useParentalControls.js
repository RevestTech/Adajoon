/**
 * Hook for managing parental controls and kids mode.
 */
import { useState, useEffect } from 'react';
import { authenticatedFetch } from '../utils/csrf';
import { isPinUnlocked, setPinUnlocked, clearPinUnlock } from '../utils/parental';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function useParentalControls() {
  const [kidsModeEnabled, setKidsModeEnabled] = useState(false);
  const [hasPin, setHasPin] = useState(false);
  const [pinUnlocked, setPinUnlockedState] = useState(false);
  const [loading, setLoading] = useState(true);

  /**
   * Load parental control status from server.
   */
  const loadStatus = async () => {
    setLoading(true);
    
    try {
      const response = await authenticatedFetch(`${API_URL}/api/parental/status`);
      if (response.ok) {
        const data = await response.json();
        setKidsModeEnabled(data.kids_mode_enabled);
        setHasPin(data.has_pin);
        setPinUnlockedState(isPinUnlocked());
      }
    } catch (error) {
      console.error('Failed to load parental status:', error);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Set or update parental PIN.
   */
  const setPin = async (pin) => {
    try {
      const response = await authenticatedFetch(`${API_URL}/api/parental/set-pin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pin }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to set PIN');
      }
      
      setHasPin(true);
      return true;
    } catch (error) {
      console.error('Failed to set PIN:', error);
      throw error;
    }
  };

  /**
   * Verify parental PIN.
   */
  const verifyPin = async (pin) => {
    try {
      const response = await authenticatedFetch(`${API_URL}/api/parental/verify-pin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pin }),
      });
      
      if (!response.ok) {
        return false;
      }
      
      // Mark as unlocked in session
      setPinUnlocked();
      setPinUnlockedState(true);
      return true;
    } catch (error) {
      console.error('PIN verification failed:', error);
      return false;
    }
  };

  /**
   * Toggle kids mode on/off.
   */
  const toggleKidsMode = async (enabled) => {
    try {
      const response = await authenticatedFetch(`${API_URL}/api/parental/kids-mode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to toggle kids mode');
      }
      
      const data = await response.json();
      setKidsModeEnabled(data.kids_mode_enabled);
      
      // Clear unlock state when enabling kids mode
      if (enabled) {
        clearPinUnlock();
        setPinUnlockedState(false);
      }
      
      return true;
    } catch (error) {
      console.error('Failed to toggle kids mode:', error);
      return false;
    }
  };

  /**
   * Remove PIN (requires verification first).
   */
  const removePin = async () => {
    try {
      const response = await authenticatedFetch(`${API_URL}/api/parental/pin`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error('Failed to remove PIN');
      }
      
      setHasPin(false);
      setKidsModeEnabled(false);
      clearPinUnlock();
      setPinUnlockedState(false);
      return true;
    } catch (error) {
      console.error('Failed to remove PIN:', error);
      return false;
    }
  };

  /**
   * Lock adult content (clear session unlock).
   */
  const lock = () => {
    clearPinUnlock();
    setPinUnlockedState(false);
  };

  // Load status on mount
  useEffect(() => {
    loadStatus();
  }, []);

  return {
    kidsModeEnabled,
    hasPin,
    pinUnlocked,
    loading,
    setPin,
    verifyPin,
    toggleKidsMode,
    removePin,
    lock,
    reload: loadStatus,
  };
}
