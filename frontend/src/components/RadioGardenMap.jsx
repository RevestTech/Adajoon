import { useCallback, useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { fetchRadioMap, fetchRadioMapRide, fetchRadioStations } from "../api/radio";
import "./RadioGardenMap.css";

const DEFAULT_STYLE =
  import.meta.env.VITE_MAP_STYLE_URL || "https://tiles.openfreemap.org/styles/dark";

const FETCH_DEBOUNCE_MS = 280;

/** OpenFreeMap dark is near-black; lift land/water/roads so geography is readable. */
function enhanceDarkBasemap(map) {
  const tweaks = [
    ["background", "background-color", "#152033"],
    ["water", "fill-color", "#0d1624"],
    ["landuse_residential", "fill-color", "#1a2438"],
    ["landcover_wood", "fill-color", "#1c2a1f"],
    ["landuse_park", "fill-color", "#1a2a22"],
    ["boundary_country_z0-4", "line-color", "#5a6d90"],
    ["boundary_country_z5-", "line-color", "#5a6d90"],
    ["boundary_state", "line-color", "#455878"],
    ["highway_motorway_subtle", "line-color", "#4a5a72"],
    ["highway_major_subtle", "line-color", "#3f4f68"],
    ["highway_minor", "line-color", "#344256"],
    ["highway_path", "line-color", "#2e3a4c"],
  ];
  for (const [id, prop, value] of tweaks) {
    if (!map.getLayer(id)) continue;
    try {
      map.setPaintProperty(id, prop, value);
    } catch {
      /* some paints are zoom expressions — skip safely */
    }
  }
}

/** Style references Maki icons (e.g. circle-11) not present in OFM sprites. */
function stubMissingStyleImage(map, imageId) {
  if (!imageId || map.hasImage(imageId)) return;
  const size = 16;
  const data = new Uint8Array(size * size * 4);
  // Soft visible dot for place markers so cities aren't invisible
  if (String(imageId).includes("circle")) {
    const cx = size / 2;
    const cy = size / 2;
    const r = 3.5;
    for (let y = 0; y < size; y += 1) {
      for (let x = 0; x < size; x += 1) {
        const dx = x + 0.5 - cx;
        const dy = y + 0.5 - cy;
        if (dx * dx + dy * dy <= r * r) {
          const i = (y * size + x) * 4;
          data[i] = 180;
          data[i + 1] = 200;
          data[i + 2] = 230;
          data[i + 3] = 220;
        }
      }
    }
  }
  map.addImage(imageId, { width: size, height: size, data }, { pixelRatio: 1 });
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

/** MapLibre can report lng outside [-180,180] at low zoom; clamp for the API. */
function bboxFromBounds(bounds) {
  return [
    clamp(bounds.getWest(), -180, 180),
    clamp(bounds.getSouth(), -90, 90),
    clamp(bounds.getEast(), -180, 180),
    clamp(bounds.getNorth(), -90, 90),
  ].join(",");
}

function formatClusterCount(count) {
  if (count >= 1000) return `${Math.round(count / 100) / 10}k`;
  return String(count);
}

async function resolveStationFromPin(pin) {
  const data = await fetchRadioStations({
    query: pin.name,
    country: pin.country_code || undefined,
    status: "hide_offline",
    perPage: 40,
  });
  const match = (data.stations || []).find((s) => s.id === pin.id);
  if (match) return match;

  // Name search can miss exact id; retry without country filter.
  if (pin.country_code) {
    const fallback = await fetchRadioStations({
      query: pin.name,
      status: "hide_offline",
      perPage: 40,
    });
    const found = (fallback.stations || []).find((s) => s.id === pin.id);
    if (found) return found;
  }

  throw new Error("Station stream not found");
}

export default function RadioGardenMap({ onSelect }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const markersRef = useRef([]);
  const abortRef = useRef(null);
  const debounceRef = useRef(null);
  const onSelectRef = useRef(onSelect);

  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [riding, setRiding] = useState(false);
  const [resolving, setResolving] = useState(false);

  useEffect(() => {
    onSelectRef.current = onSelect;
  }, [onSelect]);

  const clearMarkers = useCallback(() => {
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];
  }, []);

  const handleStationClick = useCallback(async (pin) => {
    setError("");
    setResolving(true);
    setStatus(`Loading ${pin.name}…`);
    try {
      const station = await resolveStationFromPin(pin);
      onSelectRef.current?.(station);
      setStatus(station.name);
    } catch (err) {
      setError(err?.message || "Could not play this station");
      setStatus("");
    } finally {
      setResolving(false);
    }
  }, []);

  const renderItems = useCallback(
    (payload) => {
      const map = mapRef.current;
      if (!map) return;

      clearMarkers();
      const items = payload.items || [];

      if (payload.type === "clusters") {
        items.forEach((cluster) => {
          const el = document.createElement("button");
          el.type = "button";
          el.className = "radio-garden-map__cluster";
          el.textContent = formatClusterCount(cluster.count);
          el.setAttribute("aria-label", `${cluster.count} stations`);
          el.addEventListener("click", (e) => {
            e.stopPropagation();
            map.easeTo({
              center: [cluster.lng, cluster.lat],
              zoom: Math.min(map.getZoom() + 2, 14),
            });
          });

          const marker = new maplibregl.Marker({ element: el, anchor: "center" })
            .setLngLat([cluster.lng, cluster.lat])
            .addTo(map);
          markersRef.current.push(marker);
        });
        setStatus(items.length ? `${items.length} areas` : "Zoom in to find stations");
        return;
      }

      items.forEach((pin) => {
        const el = document.createElement("button");
        el.type = "button";
        el.className = "radio-garden-map__marker";
        el.title = pin.name;
        el.setAttribute("aria-label", pin.name);
        el.addEventListener("click", (e) => {
          e.stopPropagation();
          handleStationClick(pin);
        });

        const marker = new maplibregl.Marker({ element: el, anchor: "center" })
          .setLngLat([pin.geo_long, pin.geo_lat])
          .addTo(map);
        markersRef.current.push(marker);
      });
      setStatus(items.length ? `${items.length} stations` : "No stations here — pan or zoom");
    },
    [clearMarkers, handleStationClick]
  );

  const fetchViewport = useCallback(async () => {
    const map = mapRef.current;
    if (!map) return;

    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    const bbox = bboxFromBounds(map.getBounds());
    const zoom = Math.round(map.getZoom());

    try {
      setError("");
      const data = await fetchRadioMap({ bbox, zoom, signal: controller.signal });
      if (controller.signal.aborted) return;
      renderItems(data);
    } catch (err) {
      if (err?.name === "AbortError") return;
      setError(err?.message || "Failed to load map stations");
    }
  }, [renderItems]);

  const scheduleFetch = useCallback(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      fetchViewport();
    }, FETCH_DEBOUNCE_MS);
  }, [fetchViewport]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return undefined;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: DEFAULT_STYLE,
      center: [10, 25],
      zoom: 2.2,
      attributionControl: { compact: true },
      dragRotate: false,
      pitchWithRotate: false,
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    mapRef.current = map;

    const onMissingImage = (e) => {
      stubMissingStyleImage(map, e?.id);
    };

    const onReady = () => {
      enhanceDarkBasemap(map);
      scheduleFetch();
    };

    map.on("styleimagemissing", onMissingImage);
    map.on("load", onReady);
    map.on("moveend", scheduleFetch);
    map.on("zoomend", scheduleFetch);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      if (abortRef.current) abortRef.current.abort();
      clearMarkers();
      map.off("styleimagemissing", onMissingImage);
      map.off("load", onReady);
      map.off("moveend", scheduleFetch);
      map.off("zoomend", scheduleFetch);
      map.remove();
      mapRef.current = null;
    };
  }, [clearMarkers, scheduleFetch]);

  const handleRide = async () => {
    const map = mapRef.current;
    setRiding(true);
    setError("");
    setStatus("Finding a station…");
    try {
      const center = map?.getCenter();
      const station = await fetchRadioMapRide({
        lat: center?.lat,
        lng: center?.lng,
      });
      if (station?.geo_long != null && station?.geo_lat != null) {
        const lng = Number(station.geo_long);
        const lat = Number(station.geo_lat);
        if (Number.isFinite(lng) && Number.isFinite(lat) && map) {
          map.flyTo({ center: [lng, lat], zoom: Math.max(map.getZoom(), 9) });
        }
      }
      onSelectRef.current?.(station);
      setStatus(station?.name || "On air");
    } catch (err) {
      setError(err?.message || "No station found for a ride");
      setStatus("");
    } finally {
      setRiding(false);
    }
  };

  const busy = riding || resolving;

  return (
    <div className="radio-garden-map" data-testid="radio-garden-map">
      <div ref={containerRef} className="radio-garden-map__canvas" />
      {(status || error) && (
        <div
          className={`radio-garden-map__status${error ? " radio-garden-map__status--error" : ""}`}
          role={error ? "alert" : "status"}
        >
          {error || status}
        </div>
      )}
      <button
        type="button"
        className="radio-garden-map__ride"
        onClick={handleRide}
        disabled={busy}
        aria-busy={busy}
      >
        {riding ? "Taking a ride…" : "Take a ride"}
      </button>
    </div>
  );
}
