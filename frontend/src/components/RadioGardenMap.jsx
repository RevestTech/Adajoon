import { useCallback, useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { fetchRadioMap, fetchRadioMapRide } from "../api/radio";

const DEFAULT_STYLE =
  import.meta.env.VITE_MAP_STYLE_URL ||
  "https://demotiles.maplibre.org/style.json";

export default function RadioGardenMap({ onSelectStation, selectedStation }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const markersRef = useRef([]);
  const fetchTimer = useRef(null);
  const [nowPlaying, setNowPlaying] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [rideLoading, setRideLoading] = useState(false);

  const clearMarkers = () => {
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];
  };

  const loadViewport = useCallback(async () => {
    const map = mapRef.current;
    if (!map) return;
    const bounds = map.getBounds();
    const zoom = Math.round(map.getZoom());
    setLoading(true);
    setError("");
    try {
      const data = await fetchRadioMap({
        west: bounds.getWest(),
        south: bounds.getSouth(),
        east: bounds.getEast(),
        north: bounds.getNorth(),
        zoom,
        limit: 400,
      });
      clearMarkers();
      if (data.type === "clusters") {
        data.items.forEach((c) => {
          const el = document.createElement("button");
          el.type = "button";
          el.className = "rg-cluster";
          el.textContent = String(c.count);
          el.title = `${c.count} stations near ${c.sample_name || ""}`;
          el.addEventListener("click", (e) => {
            e.stopPropagation();
            map.easeTo({ center: [c.lng, c.lat], zoom: Math.min(zoom + 2, 12) });
          });
          const marker = new maplibregl.Marker({ element: el })
            .setLngLat([c.lng, c.lat])
            .addTo(map);
          markersRef.current.push(marker);
        });
      } else {
        data.items.forEach((st) => {
          const lat = parseFloat(st.geo_lat);
          const lng = parseFloat(st.geo_long);
          if (Number.isNaN(lat) || Number.isNaN(lng)) return;
          const el = document.createElement("button");
          el.type = "button";
          el.className = "rg-dot";
          el.title = st.name;
          el.addEventListener("click", (e) => {
            e.stopPropagation();
            setNowPlaying(st);
            onSelectStation?.(st);
          });
          const marker = new maplibregl.Marker({ element: el })
            .setLngLat([lng, lat])
            .addTo(map);
          markersRef.current.push(marker);
        });
      }
    } catch (err) {
      setError(err.message || "Failed to load stations");
    } finally {
      setLoading(false);
    }
  }, [onSelectStation]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: DEFAULT_STYLE,
      center: [0, 20],
      zoom: 2,
      attributionControl: true,
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    mapRef.current = map;

    const scheduleFetch = () => {
      clearTimeout(fetchTimer.current);
      fetchTimer.current = setTimeout(() => {
        loadViewport();
      }, 280);
    };

    map.on("load", scheduleFetch);
    map.on("moveend", scheduleFetch);

    return () => {
      clearTimeout(fetchTimer.current);
      clearMarkers();
      map.remove();
      mapRef.current = null;
    };
  }, [loadViewport]);

  useEffect(() => {
    if (selectedStation) setNowPlaying(selectedStation);
  }, [selectedStation]);

  const handleRide = async () => {
    const map = mapRef.current;
    setRideLoading(true);
    try {
      const center = map?.getCenter();
      const station = await fetchRadioMapRide({
        lat: center?.lat,
        lng: center?.lng,
      });
      setNowPlaying(station);
      onSelectStation?.(station);
      const lat = parseFloat(station.geo_lat);
      const lng = parseFloat(station.geo_long);
      if (map && !Number.isNaN(lat) && !Number.isNaN(lng)) {
        map.easeTo({ center: [lng, lat], zoom: Math.max(map.getZoom(), 6) });
      }
    } catch (err) {
      setError(err.message || "Ride failed");
    } finally {
      setRideLoading(false);
    }
  };

  return (
    <div className="radio-garden-map">
      <div ref={containerRef} className="radio-garden-map__canvas" />
      <div className="radio-garden-map__reticle" aria-hidden="true" />
      {(nowPlaying || selectedStation) && (
        <div className="radio-garden-map__now">
          {(nowPlaying || selectedStation)?.name}
        </div>
      )}
      <div className="radio-garden-map__footer">
        <button
          type="button"
          className="radio-garden-map__ride"
          onClick={handleRide}
          disabled={rideLoading}
        >
          {rideLoading ? "Finding…" : "Take a ride"}
        </button>
      </div>
      {loading && <div className="radio-garden-map__status">Loading stations…</div>}
      {error && <div className="radio-garden-map__error">{error}</div>}
    </div>
  );
}
