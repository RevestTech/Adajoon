# Floating Player Feature

## Overview

Adajoon supports two pop-out modes:

1. **TV — in-page floating player**: Draggable/resizable overlay on the same tab (desktop).
2. **Radio — browser window**: Opens a dedicated popup window with a mini player (`/?radio_popout=1`). If the browser blocks popups, falls back to the in-page floating player.

## Features

### Core functionality
- **Pop-out Mode**: Click the pop-out control in player chrome
- **TV**: In-page floating window (drag header, resize corner)
- **Radio**: New browser window with stream controls; main-tab audio stops
- **Dock Back** (TV / radio floating fallback): Return to the main modal player
- **Persistent State** (in-page floating): Position and size saved to localStorage

### Controls
- **Play/Pause**: Control playback without docking
- **Country Info**: View channel/station country in the header (floating)
- **Dock Button**: Return to full modal view (in-page floating)
- **Close Button**: Stop playback and close
- **Keyboard**: Press `Escape` to close the floating player (in-page)

### Device support
- **Desktop Only**: Pop-out controls are only wired on desktop (`device.isDesktop`)
- **Hidden on Mobile/TV**: Automatically disabled

## Usage

### For TV Channels

1. Open any TV channel
2. Click the **"Pop Out"** button in the top-right controls
3. The video player becomes a floating window in the same tab
4. Drag to reposition, resize from the corner
5. Click **"Dock"** to return to normal view, or **×** to close

### For Radio Stations

1. Open any radio station (grid, map pin, or Take a ride)
2. Click **"Open in new window"** (pop-out icon)
3. A browser popup opens with art, title, and audio controls
4. Allow popups for adajoon.com if the browser blocks the window (otherwise the in-page floater is used)

## Technical Implementation

### Radio browser window
- `frontend/src/utils/radioPopout.js` — stash station in `localStorage`, `window.open`
- `frontend/src/components/RadioPopoutWindow.jsx` — standalone mini UI
- `frontend/src/main.jsx` — when `?radio_popout=1`, render popout instead of full `App`

### In-page floating (TV + radio fallback)
- **`FloatingPlayer.jsx`**: Draggable/resizable overlay
- Supports `variant="tv"` and `variant="radio"`
- Shares video/audio refs with modal players for seamless transitions

### State Management
- `floatingTv` / `floatingRadio` state in `App.jsx` (in-page floater)
- Position saved to `localStorage` as `adajoon_floating_position`
- Size saved to `localStorage` as `adajoon_floating_size`
- Radio popup payload: `adajoon_radio_popout:{stationId}` (short TTL)

### Integration Points
```javascript
// VideoPlayer integration
<VideoPlayer
  onPopOut={device.isDesktop ? handlePopOutTv : undefined}
  // ... other props
/>

// Radio — opens browser window (falls back to FloatingPlayer if blocked)
<RadioPlayer
  onPopOut={device.isDesktop ? handlePopOutRadio : undefined}
/>
```

## Related

- Radio map + EPG: `docs/RADIO_MAP_EPG.md`
