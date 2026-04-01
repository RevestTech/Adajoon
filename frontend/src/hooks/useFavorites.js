import { useState, useCallback, useEffect } from "react";

const STORAGE_KEY = "adajoon_favorites";
const RADIO_STORAGE_KEY = "adajoon_radio_favorites";

function load(key) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

export default function useFavorites() {
  const [favorites, setFavorites] = useState(() => load(STORAGE_KEY));

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(favorites));
  }, [favorites]);

  const toggleFavorite = useCallback((channel) => {
    setFavorites((prev) => {
      const next = { ...prev };
      if (next[channel.id]) {
        delete next[channel.id];
      } else {
        next[channel.id] = {
          id: channel.id,
          name: channel.name,
          logo: channel.logo,
          country_code: channel.country_code,
          categories: channel.categories,
          stream_url: channel.stream_url,
        };
      }
      return next;
    });
  }, []);

  const isFavorite = useCallback(
    (channelId) => !!favorites[channelId],
    [favorites]
  );

  const favoritesList = Object.values(favorites);
  const favoritesCount = favoritesList.length;

  return { favorites, favoritesList, favoritesCount, toggleFavorite, isFavorite };
}

export function useRadioFavorites() {
  const [favorites, setFavorites] = useState(() => load(RADIO_STORAGE_KEY));

  useEffect(() => {
    localStorage.setItem(RADIO_STORAGE_KEY, JSON.stringify(favorites));
  }, [favorites]);

  const toggleFavorite = useCallback((station) => {
    setFavorites((prev) => {
      const next = { ...prev };
      if (next[station.id]) {
        delete next[station.id];
      } else {
        next[station.id] = {
          id: station.id,
          name: station.name,
          favicon: station.favicon,
          country_code: station.country_code,
          country: station.country,
          tags: station.tags,
          url: station.url,
          url_resolved: station.url_resolved,
          bitrate: station.bitrate,
          codec: station.codec,
          language: station.language,
          homepage: station.homepage,
          last_check_ok: station.last_check_ok,
        };
      }
      return next;
    });
  }, []);

  const isFavorite = useCallback(
    (stationId) => !!favorites[stationId],
    [favorites]
  );

  const favoritesList = Object.values(favorites);
  const favoritesCount = favoritesList.length;

  return { favoritesList, favoritesCount, toggleFavorite, isFavorite };
}
