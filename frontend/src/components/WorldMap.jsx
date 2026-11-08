import React, { useState, useRef, useEffect, useCallback } from 'react';
import { worldMapPaths } from '../data/worldMapPaths';

const WorldMap = ({
  mode = 'tv',
  countries = [],
  radioCountries = [],
  activeCountries = [],
  onSelectCountry = () => {},
  onSelectChannel = () => {},
  onSelectStation = () => {},
}) => {
  const svgRef = useRef(null);
  const [scale, setScale] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [selectedCountry, setSelectedCountry] = useState(null);
  const [hoveredCountry, setHoveredCountry] = useState(null);
  const [touchDistance, setTouchDistance] = useState(0);

  // Build lookup maps for quick access
  const countryDataMap = new Map();
  const radioDataMap = new Map();

  countries.forEach((c) => {
    countryDataMap.set(c.code, c);
  });

  radioCountries.forEach((r) => {
    radioDataMap.set(r.country_code, r);
  });

  // Get country data based on current mode
  const getCountryData = (code) => {
    if (mode === 'tv') {
      return countryDataMap.get(code);
    } else {
      return radioDataMap.get(code);
    }
  };

  // Get count of channels/stations for a country
  const getCountryCount = (code) => {
    const data = getCountryData(code);
    if (!data) return 0;
    return mode === 'tv' ? data.channel_count : data.station_count;
  };

  // Get color intensity based on content count
  const getCountryColor = (code, isHovered = false) => {
    const count = getCountryCount(code);
    const isActive = activeCountries.includes(code);

    // Active/selected color
    if (isActive || selectedCountry === code) {
      return '#e94560';
    }

    // Empty countries
    if (count === 0) {
      return isHovered ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.05)';
    }

    // Gradient from blue to purple based on count
    // Find max count for normalization
    const allCounts = Array.from(countryDataMap.values()).map((c) => c.channel_count);
    const radioAllCounts = Array.from(radioDataMap.values()).map((c) => c.station_count);
    const maxCount = Math.max(...allCounts, ...radioAllCounts, 1);

    const intensity = Math.min(count / maxCount, 1);

    // Interpolate color: #1e3a5f (blue) to #c084fc (purple)
    const blueR = 30,
      blueG = 58,
      blueB = 95;
    const purpleR = 192,
      purpleG = 132,
      purpleB = 252;

    const r = Math.round(blueR + (purpleR - blueR) * intensity);
    const g = Math.round(blueG + (purpleG - blueG) * intensity);
    const b = Math.round(blueB + (purpleB - blueB) * intensity);

    let color = `rgb(${r}, ${g}, ${b})`;

    if (isHovered) {
      const hoverR = Math.min(r + 50, 255);
      const hoverG = Math.min(g + 50, 255);
      const hoverB = Math.min(b + 50, 255);
      color = `rgb(${hoverR}, ${hoverG}, ${hoverB})`;
    }

    return color;
  };

  // Mouse wheel zoom
  const handleWheel = useCallback(
    (e) => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      const newScale = Math.max(1, Math.min(scale * delta, 4));
      setScale(newScale);
    },
    [scale]
  );

  // Mouse drag pan
  const handleMouseDown = useCallback((e) => {
    if (e.button !== 0) return; // Only left click
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  }, [pan]);

  const handleMouseMove = useCallback(
    (e) => {
      if (!isDragging) return;
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    },
    [isDragging, dragStart]
  );

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Touch support for mobile zoom and pan
  const handleTouchStart = useCallback((e) => {
    if (e.touches.length === 2) {
      // Two-finger pinch zoom
      const dx = e.touches[0].clientX - e.touches[1].clientX;
      const dy = e.touches[0].clientY - e.touches[1].clientY;
      setTouchDistance(Math.sqrt(dx * dx + dy * dy));
    } else if (e.touches.length === 1) {
      // Single touch pan
      setIsDragging(true);
      setDragStart({ x: e.touches[0].clientX - pan.x, y: e.touches[0].clientY - pan.y });
    }
  }, [pan]);

  const handleTouchMove = useCallback(
    (e) => {
      if (e.touches.length === 2) {
        // Pinch zoom
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (touchDistance > 0) {
          const delta = distance / touchDistance;
          setScale((prev) => Math.max(1, Math.min(prev * delta, 4)));
        }
        setTouchDistance(distance);
      } else if (e.touches.length === 1 && isDragging) {
        // Pan
        setPan({
          x: e.touches[0].clientX - dragStart.x,
          y: e.touches[0].clientY - dragStart.y,
        });
      }
    },
    [isDragging, dragStart, touchDistance]
  );

  const handleTouchEnd = useCallback(() => {
    setIsDragging(false);
    setTouchDistance(0);
  }, []);

  // Attach event listeners
  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;

    svg.addEventListener('wheel', handleWheel, { passive: false });
    svg.addEventListener('mousedown', handleMouseDown);
    svg.addEventListener('mousemove', handleMouseMove);
    svg.addEventListener('mouseup', handleMouseUp);
    svg.addEventListener('mouseleave', handleMouseUp);
    svg.addEventListener('touchstart', handleTouchStart, { passive: true });
    svg.addEventListener('touchmove', handleTouchMove, { passive: true });
    svg.addEventListener('touchend', handleTouchEnd);

    return () => {
      svg.removeEventListener('wheel', handleWheel);
      svg.removeEventListener('mousedown', handleMouseDown);
      svg.removeEventListener('mousemove', handleMouseMove);
      svg.removeEventListener('mouseup', handleMouseUp);
      svg.removeEventListener('mouseleave', handleMouseUp);
      svg.removeEventListener('touchstart', handleTouchStart);
      svg.removeEventListener('touchmove', handleTouchMove);
      svg.removeEventListener('touchend', handleTouchEnd);
    };
  }, [handleWheel, handleMouseDown, handleMouseMove, handleMouseUp, handleTouchStart, handleTouchMove, handleTouchEnd]);

  // Handle country selection
  const handleCountryClick = (countryCode) => {
    setSelectedCountry(countryCode);
    onSelectCountry(countryCode);
  };

  // Find country name from paths
  const getCountryName = (code) => {
    const path = worldMapPaths.find((p) => p.id === code);
    return path ? path.name : code;
  };

  // Get selected country details
  const selectedCountryData = selectedCountry ? getCountryData(selectedCountry) : null;

  return (
    <div className="world-map-container">
      {/* SVG Map */}
      <svg
        ref={svgRef}
        className="world-map-svg"
        viewBox="0 0 1000 500"
        width="100%"
        height="100%"
        style={{
          cursor: isDragging ? 'grabbing' : 'grab',
          touchAction: 'none',
        }}
      >
        {/* Apply transform for pan and zoom */}
        <g style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})`, transformOrigin: '0 0' }}>
          {/* Render country paths */}
          {worldMapPaths.map((countryPath) => (
            <path
              key={countryPath.id}
              id={countryPath.id}
              d={countryPath.d}
              className="world-map-path"
              fill={getCountryColor(countryPath.id, hoveredCountry === countryPath.id)}
              stroke="rgba(255,255,255,0.1)"
              strokeWidth="0.5"
              style={{
                cursor: getCountryCount(countryPath.id) > 0 ? 'pointer' : 'default',
                transition: 'fill 0.2s ease',
              }}
              onMouseEnter={() => setHoveredCountry(countryPath.id)}
              onMouseLeave={() => setHoveredCountry(null)}
              onClick={() => {
                if (getCountryCount(countryPath.id) > 0) {
                  handleCountryClick(countryPath.id);
                }
              }}
            />
          ))}
        </g>

      </svg>

      {/* Big country name overlay */}
      {hoveredCountry && getCountryCount(hoveredCountry) > 0 && (
        <div className="world-map-country-label">
          <div className="world-map-country-label-name">{getCountryName(hoveredCountry)}</div>
          <div className="world-map-country-label-count">
            {getCountryCount(hoveredCountry)} {mode === 'tv' ? 'channels' : 'stations'}
          </div>
        </div>
      )}

      {/* Zoom Controls */}
      <div className="world-map-controls">
        <button
          className="world-map-zoom-btn world-map-zoom-in"
          onClick={() => setScale(Math.min(scale * 1.2, 4))}
          aria-label="Zoom in"
        >
          +
        </button>
        <button
          className="world-map-zoom-btn world-map-zoom-out"
          onClick={() => setScale(Math.max(scale / 1.2, 1))}
          aria-label="Zoom out"
        >
          -
        </button>
        <button
          className="world-map-zoom-btn world-map-zoom-reset"
          onClick={() => {
            setScale(1);
            setPan({ x: 0, y: 0 });
          }}
          aria-label="Reset view"
        >
          Reset
        </button>
      </div>

      {/* Legend */}
      <div className="world-map-legend">
        <div className="world-map-legend-title">Channels/Stations</div>
        <div className="world-map-legend-items">
          <div className="world-map-legend-item">
            <div
              className="world-map-legend-color"
              style={{ backgroundColor: 'rgba(255,255,255,0.05)' }}
            ></div>
            <span>None</span>
          </div>
          <div className="world-map-legend-item">
            <div
              className="world-map-legend-color"
              style={{ backgroundColor: '#1e3a5f' }}
            ></div>
            <span>Few</span>
          </div>
          <div className="world-map-legend-item">
            <div
              className="world-map-legend-color"
              style={{ backgroundColor: '#c084fc' }}
            ></div>
            <span>Many</span>
          </div>
          <div className="world-map-legend-item">
            <div
              className="world-map-legend-color"
              style={{ backgroundColor: '#e94560' }}
            ></div>
            <span>Selected</span>
          </div>
        </div>
      </div>

      {/* Country Preview Panel */}
      {selectedCountryData && (
        <div className="world-map-preview-panel">
          <button
            className="world-map-preview-close"
            onClick={() => setSelectedCountry(null)}
            aria-label="Close preview"
          >
            ×
          </button>

          <div className="world-map-preview-content">
            <div className="world-map-preview-header">
              <div className="world-map-preview-flag">{getFlagEmoji(selectedCountry)}</div>
              <div className="world-map-preview-info">
                <h3 className="world-map-preview-title">{getCountryName(selectedCountry)}</h3>
                <p className="world-map-preview-count">
                  {getCountryCount(selectedCountry)} {mode === 'tv' ? 'Channels' : 'Stations'}
                </p>
              </div>
            </div>

            <button
              className="world-map-preview-action-btn"
              onClick={() => {
                // Trigger callback to show channels/stations list
                if (mode === 'tv' && selectedCountryData.channel_count > 0) {
                  onSelectChannel({ countryCode: selectedCountry });
                } else if (mode === 'radio' && selectedCountryData.station_count > 0) {
                  onSelectStation({ countryCode: selectedCountry });
                }
              }}
            >
              View {mode === 'tv' ? 'Channels' : 'Stations'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Helper function to get flag emoji for country code
function getFlagEmoji(countryCode) {
  if (!countryCode || countryCode.length !== 2) return '';
  const codePoints = countryCode
    .toUpperCase()
    .split('')
    .map((char) => 127397 + char.charCodeAt(0));
  return String.fromCodePoint(...codePoints);
}

export default WorldMap;
