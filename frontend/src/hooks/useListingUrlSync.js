import { useEffect } from "react";
import { writeUrlParams } from "./useUrlState";

/**
 * Custom hook to sync listing state to URL parameters.
 * Keeps URL in sync with current filters, search, page, etc.
 */
export function useListingUrlSync({
  mode,
  tvSearch,
  radioSearch,
  activeCategories,
  activeCountries,
  activeTags,
  activeRadioCountries,
  activeQualities,
  activeRadioQualities,
  page,
  radioPage,
  viewMode,
  showFavorites,
}) {
  useEffect(() => {
    writeUrlParams({
      mode,
      q: mode === "tv" ? tvSearch : radioSearch,
      cat: activeCategories,
      country: mode === "tv" ? activeCountries : activeRadioCountries,
      tag: activeTags,
      status: mode === "tv" ? activeQualities : activeRadioQualities,
      page: mode === "tv" ? page : radioPage,
      view: viewMode,
      fav: showFavorites,
    });
  }, [
    mode,
    tvSearch,
    radioSearch,
    activeCategories,
    activeCountries,
    activeTags,
    activeRadioCountries,
    activeQualities,
    activeRadioQualities,
    page,
    radioPage,
    viewMode,
    showFavorites,
  ]);
}
