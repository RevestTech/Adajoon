/**
 * Hook for managing content recommendations.
 */
import { useState, useEffect } from 'react';
import { fetchRecommendations } from '../api/recommendations';

export default function useRecommendations(itemType, itemId) {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!itemType || !itemId) {
      setRecommendations([]);
      return;
    }

    let mounted = true;
    
    async function loadRecommendations() {
      setLoading(true);
      setError(null);
      
      try {
        const data = await fetchRecommendations(itemType, itemId, 10);
        if (mounted) {
          setRecommendations(data);
        }
      } catch (err) {
        if (mounted) {
          setError(err.message);
          setRecommendations([]);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadRecommendations();

    return () => {
      mounted = false;
    };
  }, [itemType, itemId]);

  return {
    recommendations,
    loading,
    error,
  };
}
