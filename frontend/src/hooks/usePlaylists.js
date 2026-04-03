/**
 * Hook for managing user playlists.
 */
import { useState, useEffect, useCallback } from 'react';
import {
  fetchPlaylists,
  fetchPlaylist,
  createPlaylist,
  updatePlaylist,
  deletePlaylist,
  addToPlaylist,
  removeFromPlaylist,
  reorderPlaylist,
} from '../api/playlists';

export default function usePlaylists() {
  const [playlists, setPlaylists] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Load all playlists for user.
   */
  const loadPlaylists = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await fetchPlaylists();
      setPlaylists(data);
    } catch (err) {
      setError(err.message);
      console.error('Failed to load playlists:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Create a new playlist.
   */
  const create = async (name, description = '', isPublic = false) => {
    try {
      const newPlaylist = await createPlaylist(name, description, isPublic);
      setPlaylists((prev) => [newPlaylist, ...prev]);
      return newPlaylist;
    } catch (err) {
      setError(err.message);
      console.error('Failed to create playlist:', err);
      return null;
    }
  };

  /**
   * Update playlist metadata.
   */
  const update = async (playlistId, updates) => {
    try {
      const updated = await updatePlaylist(playlistId, updates);
      setPlaylists((prev) =>
        prev.map((p) => (p.id === playlistId ? { ...p, ...updated } : p))
      );
      return updated;
    } catch (err) {
      setError(err.message);
      console.error('Failed to update playlist:', err);
      return null;
    }
  };

  /**
   * Delete a playlist.
   */
  const remove = async (playlistId) => {
    try {
      await deletePlaylist(playlistId);
      setPlaylists((prev) => prev.filter((p) => p.id !== playlistId));
      return true;
    } catch (err) {
      setError(err.message);
      console.error('Failed to delete playlist:', err);
      return false;
    }
  };

  /**
   * Add item to playlist.
   */
  const addItem = async (playlistId, itemType, itemId, itemData) => {
    try {
      await addToPlaylist(playlistId, itemType, itemId, itemData);
      
      // Increment item count in local state
      setPlaylists((prev) =>
        prev.map((p) =>
          p.id === playlistId ? { ...p, item_count: (p.item_count || 0) + 1 } : p
        )
      );
      
      return true;
    } catch (err) {
      setError(err.message);
      console.error('Failed to add item to playlist:', err);
      return false;
    }
  };

  /**
   * Remove item from playlist.
   */
  const removeItem = async (playlistId, itemId) => {
    try {
      await removeFromPlaylist(playlistId, itemId);
      
      // Decrement item count
      setPlaylists((prev) =>
        prev.map((p) =>
          p.id === playlistId ? { ...p, item_count: Math.max(0, (p.item_count || 0) - 1) } : p
        )
      );
      
      return true;
    } catch (err) {
      setError(err.message);
      console.error('Failed to remove item from playlist:', err);
      return false;
    }
  };

  // Auto-load on mount
  useEffect(() => {
    loadPlaylists();
  }, [loadPlaylists]);

  return {
    playlists,
    loading,
    error,
    loadPlaylists,
    create,
    update,
    remove,
    addItem,
    removeItem,
  };
}
