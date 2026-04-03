import { useState, useEffect, useCallback, useRef } from "react";
import { fetchRadioStations, fetchRadioTags, fetchRadioCountries } from "../api/radio";

/**
 * Custom hook for managing radio stations state and logic.
 */
export function useRadioStations(initialState = {}) {
  const [stations, setStations] = useState([]);
  const [tags, setTags] = useState([]);
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [search, setSearch] = useState(initialState.search || "");
  const [activeTags, setActiveTags] = useState(initialState.activeTags || []);
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

  // Load metadata (tags, countries)
  const loadMetadata = useCallback(async () => {
    try {
      const [tgs, ctrs] = await Promise.all([
        fetchRadioTags(),
        fetchRadioCountries(),
      ]);
      setTags(tgs);
      setCountries(ctrs);
    } catch (err) {
      console.error("Failed to load radio metadata:", err);
    }
  }, []);

  // Load stations with filters
  const loadStations = useCallback(async () => {
    if (showFavorites) return;
    if (stations.length === 0) setLoading(true);
    setError(null);
    
    try {
      const data = await fetchRadioStations({
        query: search || undefined,
        tag: activeTags.length ? activeTags.join(",") : undefined,
        country: activeCountries.length ? activeCountries.join(",") : undefined,
        status: activeQualities.length ? activeQualities.join(",") : undefined,
        page,
      });
      
      setStations(data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }, [search, activeTags, activeCountries, activeQualities, page, showFavorites]);

  // Reset page when filters change
  useEffect(() => {
    const key = `${debouncedSearch}|${activeTags.join(",")}|${activeCountries.join(",")}|${activeQualities.join(",")}`;
    if (prevFiltersKey.current !== null && prevFiltersKey.current !== key) {
      setPage(1);
    }
    prevFiltersKey.current = key;
  }, [debouncedSearch, activeTags, activeCountries, activeQualities]);

  // Clear filters helper
  const clearFilter = useCallback((filterType, value) => {
    switch (filterType) {
      case "search":
        setSearch("");
        break;
      case "tag":
        setActiveTags(prev => prev.filter(t => t !== value));
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
    setActiveTags([]);
    setActiveCountries([]);
    setActiveQualities([]);
    setPage(1);
  }, []);

  return {
    // Data
    stations,
    tags,
    countries,
    loading,
    error,
    
    // Search & filters
    search,
    setSearch,
    debouncedSearch,
    activeTags,
    setActiveTags,
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
    loadStations,
  };
}
