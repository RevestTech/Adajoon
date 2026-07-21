import { useEffect, useRef } from "react";
import { analytics } from "../analytics";

/**
 * Emit Screen View / Navigation whenever the user moves between app surfaces.
 */
export function useNavigationTracking({
  mode,
  mapSubMode,
  query,
  showFavorites,
  showAISearch,
  showAdminDashboard,
  showLogin,
  selectedChannelId,
  selectedStationId,
  isGuest,
}) {
  const prevScreenRef = useRef(null);

  useEffect(() => {
    let screen = mode || "unknown";
    if (showLogin) screen = "login";
    else if (showAdminDashboard) screen = "admin";
    else if (showAISearch) screen = `ai_search:${mode === "map" ? mapSubMode : mode}`;
    else if (showFavorites) screen = `favorites:${mode === "map" ? mapSubMode : mode}`;
    else if (mode === "map") screen = `map:${mapSubMode || "tv"}`;
    else if (selectedChannelId) screen = "player:tv";
    else if (selectedStationId) screen = "player:radio";
    else screen = mode;

    const props = {
      mode,
      map_sub_mode: mapSubMode || null,
      query: query ? String(query).slice(0, 120) : "",
      is_guest: Boolean(isGuest),
      has_tv_player: Boolean(selectedChannelId),
      has_radio_player: Boolean(selectedStationId),
    };

    const prev = prevScreenRef.current;
    if (prev && prev !== screen) {
      analytics.trackNavigation(prev, screen, props);
    }
    analytics.trackScreen(screen, props);
    prevScreenRef.current = screen;
  }, [
    mode,
    mapSubMode,
    query,
    showFavorites,
    showAISearch,
    showAdminDashboard,
    showLogin,
    selectedChannelId,
    selectedStationId,
    isGuest,
  ]);
}
