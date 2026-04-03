/**
 * Recommendations API client.
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Fetch recommendations similar to a channel or station.
 * @param {string} itemType - 'tv' or 'radio'
 * @param {string} itemId - Channel or station ID
 * @param {number} limit - Max recommendations (default: 10)
 */
export async function fetchRecommendations(itemType, itemId, limit = 10) {
  try {
    const response = await fetch(`${API_URL}/api/recommendations/similar`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        item_type: itemType,
        item_id: itemId,
        limit,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch recommendations: ${response.status}`);
    }

    const data = await response.json();
    return data.recommendations || [];
  } catch (error) {
    console.error('Error fetching recommendations:', error);
    return [];
  }
}
