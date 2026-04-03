import { useState, useEffect, useCallback, useRef } from "react";
import { fetchChannels, fetchCategories, fetchCountries, fetchStats } from "../api/channels";

/**
 * Custom hook for managing TV channels state and logic.
 */
export function useTvChannels(initialState = {}) {
  const [channels, setChannels] = useState([]);
  const [categories, setCategories] = useState([]);
  const [countries, setCountries] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [search, setSearch] = useState(initialState.search || "");
  const [activeCategories, setActiveCategories] = useState(initialState.activeCategories || []);
  const [activeCountries, setActiveCountries] = useState(initialState.activeCountries || []);
  const [activeQualities, setActiveQualities] = useState(initialState.activeQualities || []);
  const [page, setPage] = useState(initialState.page || 1);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [showFavorites, setShowFavorites] = useState(initialState.showFavorites || false);
  
  const [debouncedSearch, setDebouncedSearch] = useState(search);
  const prevFiltersKey = useRef(null);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  // Load metadata (categories, countries, stats)
  const loadMetadata = useCallback(async () => {
    try {
      const [cats, ctrs, sts] = await Promise.all([
        fetchCategories(),
        fetchCountries(),
        fetchStats(),
      ]);
      setCategories(cats);
      setCountries(ctrs);
      setStats(sts);
    } catch (err) {
      console.error("Failed to load TV metadata:", err);
    }
  }, []);

  // Load channels with filters
  const loadChannels = useCallback(async () => {
    if (showFavorites) return;
    if (channels.length === 0) setLoading(true);
    setError(null);
    
    try {
      const data = await fetchChannels({
        query: search || undefined,
        category: activeCategories.length ? activeCategories.join(",") : undefined,
        country: activeCountries.length ? activeCountries.join(",") : undefined,
        status: activeQualities.length ? activeQualities.join(",") : undefined,
        page,
      });
      
      setChannels(data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }, [search, activeCategories, activeCountries, activeQualities, page, showFavorites]);

  // Reset page when filters change
  useEffect(() => {
    const key = `${debouncedSearch}|${activeCategories.join(",")}|${activeCountries.join(",")}|${activeQualities.join(",")}`;
    if (prevFiltersKey.current !== null && prevFiltersKey.current !== key) {
      setPage(1);
    }
    prevFiltersKey.current = key;
  }, [debouncedSearch, activeCategories, activeCountries, activeQualities]);

  // Clear filters helper
  const clearFilter = useCallback((filterType, value) => {
    switch (filterType) {
      case "search":
        setSearch("");
        break;
      case "category":
        setActiveCategories(prev => prev.filter(c => c !== value));
        break;
      case "country":
        setActiveCountries(prev => prev.filter(c => c !== value));
        break;
      case "quality":
        setActiveQualities(prev => prev.filter(q => q !== value));
        break;
    }
  }, []);

  const clearAllFilters = useCallback(() => {
    setSearch("");
    setActiveCategories([]);
    setActiveCountries([]);
    setActiveQualities([]);
    setPage(1);
  }, []);

  return {
    // Data
    channels,
    categories,
    countries,
    stats,
    loading,
    error,
    
    // Search & filters
    search,
    setSearch,
    debouncedSearch,
    activeCategories,
    setActiveCategories,
    activeCountries,
    setActiveCountries,
    activeQualities,
    setActiveQualities,
    clearFilter,
    clearAllFilters,
    
    // Pagination
    page,
    setPage,
    totalPages,
    setTotalPages,
    total,
    setTotal,
    
    // Favorites
    showFavorites,
    setShowFavorites,
    
    // Actions
    loadMetadata,
    loadChannels,
  };
}
