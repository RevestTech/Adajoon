/**
 * Hook for managing parental controls and kids mode.
 */
import { useState, useEffect } from 'react';
import { authenticatedFetch } from '../utils/csrf';
import { isPinUnlocked, setPinUnlocked, clearPinUnlock } from '../utils/parental';

const BASE = '/api';

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
      const response = await authenticatedFetch(`${BASE}/parental/status`);
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
      const response = await authenticatedFetch(`${BASE}/parental/set-pin`, {
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
      const response = await authenticatedFetch(`${BASE}/parental/verify-pin`, {
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
   * Toggle kids mode on/off. Disabling it requires `pin` when a PIN is set -
   * the server enforces this regardless (see parental.py's toggle_kids_mode),
   * this is just so callers can surface the server's rejection.
   */
  const toggleKidsMode = async (enabled, pin) => {
    try {
      const response = await authenticatedFetch(`${BASE}/parental/kids-mode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled, ...(pin ? { pin } : {}) }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to toggle kids mode');
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
      throw error;
    }
  };

  /**
   * Remove PIN (server re-verifies the PIN before removing it).
   */
  const removePin = async (pin) => {
    try {
      const response = await authenticatedFetch(`${BASE}/parental/pin`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pin }),
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
