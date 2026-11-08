import { useState, useCallback, useEffect, useRef } from "react";
import { fetchChannels, fetchCategories, fetchCountries } from "../api/channels";
import { fetchRadioStations, fetchRadioTags, fetchRadioCountries } from "../api/radio";

// TV and radio both browse a paginated, filterable list: fetch facets
// (categories/tags + countries) once, fetch a page of items against the
// current filters, and reset to page 1 whenever a filter changes. The two
// verticals use this identical shape - this hook is that shape, parametrized
// by `type`. It deliberately does NOT own selection, player/modal, or
// favorites-view state: those differ enough between TV and radio
// (channel-stepping, radio's popout-window fallback, radio's eager-vs-lazy
// fetch gating) that forcing them in here would trade a correct abstraction
// for a leaky one. Callers also decide *when* to trigger loadMeta/loadList
// (TV loads eagerly on mount; radio only once its mode is active) - this
// hook just provides the state and the fetchers.
//
// Matches pre-refactor behavior exactly: the list fetch (and the
// page-reset-on-filter-change check) uses the raw `search` value, not a
// debounced one - only the separately-exposed `debouncedSearch` (used for
// URL-bar sync) is debounced. Every keystroke re-fetches; that was already
// true before this hook existed and isn't something this refactor changes.
export default function useCatalogList(
  type,
  {
    skipFetch = false,
    initialSearch = "",
    initialFacets = [],
    initialCountries = [],
    initialQualities = [],
    initialPage = 1,
  } = {}
) {
  const [items, setItems] = useState([]);
  const [facets, setFacets] = useState([]); // categories (tv) / tags (radio)
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState(initialSearch);
  const [debouncedSearch, setDebouncedSearch] = useState(initialSearch);
  const [activeFacets, setActiveFacets] = useState(initialFacets);
  const [activeCountries, setActiveCountries] = useState(initialCountries);
  const [activeQualities, setActiveQualities] = useState(initialQualities);
  const [page, setPage] = useState(initialPage);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(t);
  }, [search]);

  const loadMeta = useCallback(async () => {
    try {
      const [facetList, countryList] =
        type === "tv"
          ? await Promise.all([fetchCategories(), fetchCountries()])
          : await Promise.all([fetchRadioTags(), fetchRadioCountries()]);
      setFacets(facetList);
      setCountries(countryList);
    } catch {
      /* retry later */
    }
  }, [type]);

  const loadList = useCallback(async () => {
    if (skipFetch) return;
    // Always show the loading state while a fetch is in flight, even when
    // items are already populated - otherwise a filter change renders the
    // stale, now-mismatched list/count for a frame before new data arrives.
    setLoading(true);
    setError(null);
    try {
      const params = {
        query: search || undefined,
        country: activeCountries.length ? activeCountries.join(",") : undefined,
        status: activeQualities.length ? activeQualities.join(",") : undefined,
        page,
      };
      const data =
        type === "tv"
          ? await fetchChannels({ ...params, category: activeFacets.length ? activeFacets.join(",") : undefined })
          : await fetchRadioStations({ ...params, tag: activeFacets.length ? activeFacets.join(",") : undefined });
      setItems(type === "tv" ? data.channels : data.stations);
      setTotalPages(data.total_pages);
      setTotal(data.total);
    } catch {
      setError(
        type === "tv"
          ? "Unable to load channels. The server may still be syncing data."
          : "Unable to load radio stations. Data may still be syncing."
      );
    } finally {
      setLoading(false);
    }
  }, [type, skipFetch, search, activeFacets, activeCountries, activeQualities, page]);

  const prevFiltersKey = useRef(null);
  useEffect(() => {
    const key = JSON.stringify({ search, activeFacets, activeCountries, activeQualities, skipFetch });
    if (prevFiltersKey.current === null) {
      prevFiltersKey.current = key;
      return;
    }
    if (prevFiltersKey.current !== key) {
      prevFiltersKey.current = key;
      setPage(1);
    }
  }, [search, activeFacets, activeCountries, activeQualities, skipFetch]);

  return {
    items,
    facets,
    countries,
    loading,
    error,
    search,
    setSearch,
    debouncedSearch,
    activeFacets,
    setActiveFacets,
    activeCountries,
    setActiveCountries,
    activeQualities,
    setActiveQualities,
    page,
    setPage,
    totalPages,
    total,
    loadMeta,
    loadList,
  };
}
