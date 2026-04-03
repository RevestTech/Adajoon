/**
 * Playlists API client.
 */
import { authenticatedFetch } from '../utils/csrf';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Fetch all playlists for current user.
 */
export async function fetchPlaylists() {
  const response = await authenticatedFetch(`${API_URL}/api/playlists/`);
  if (!response.ok) {
    throw new Error(`Failed to fetch playlists: ${response.status}`);
  }
  return await response.json();
}

/**
 * Fetch single playlist details with items.
 */
export async function fetchPlaylist(playlistId) {
  const response = await authenticatedFetch(`${API_URL}/api/playlists/${playlistId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch playlist: ${response.status}`);
  }
  return await response.json();
}

/**
 * Create a new playlist.
 */
export async function createPlaylist(name, description = '', isPublic = false) {
  const response = await authenticatedFetch(`${API_URL}/api/playlists/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name,
      description,
      is_public: isPublic,
    }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to create playlist: ${response.status}`);
  }
  
  return await response.json();
}

/**
 * Update playlist metadata.
 */
export async function updatePlaylist(playlistId, updates) {
  const response = await authenticatedFetch(`${API_URL}/api/playlists/${playlistId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to update playlist: ${response.status}`);
  }
  
  return await response.json();
}

/**
 * Delete a playlist.
 */
export async function deletePlaylist(playlistId) {
  const response = await authenticatedFetch(`${API_URL}/api/playlists/${playlistId}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    throw new Error(`Failed to delete playlist: ${response.status}`);
  }
  
  return await response.json();
}

/**
 * Add item to playlist.
 */
export async function addToPlaylist(playlistId, itemType, itemId, itemData) {
  const response = await authenticatedFetch(`${API_URL}/api/playlists/${playlistId}/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      item_type: itemType,
      item_id: itemId,
      item_data: JSON.stringify(itemData),
    }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to add item to playlist: ${response.status}`);
  }
  
  return await response.json();
}

/**
 * Remove item from playlist.
 */
export async function removeFromPlaylist(playlistId, itemId) {
  const response = await authenticatedFetch(
    `${API_URL}/api/playlists/${playlistId}/items/${itemId}`,
    { method: 'DELETE' }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to remove item from playlist: ${response.status}`);
  }
  
  return await response.json();
}

/**
 * Reorder playlist items.
 */
export async function reorderPlaylist(playlistId, itemIds) {
  const response = await authenticatedFetch(`${API_URL}/api/playlists/${playlistId}/reorder`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ item_ids: itemIds }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to reorder playlist: ${response.status}`);
  }
  
  return await response.json();
}
