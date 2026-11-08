# TV Optimization Guide

## Overview

Adajoon is now optimized to run on Smart TVs, including Samsung Tizen TVs, LG webOS, and other TV browsers. The application automatically detects when it's running on a TV and adapts the interface for 10-foot viewing and remote control navigation.

## Features

### Automatic Device Detection
- Detects Samsung Tizen, LG webOS, Sony Bravia, and other TV platforms
- Automatically applies TV-optimized styles and navigation
- Shows TV mode indicator badge in top-right corner

### TV-Optimized UI
- **10-foot UI**: Larger text (24px base, up to 48px for headings)
- **Bigger buttons**: Minimum 60px height with larger padding
- **Enhanced focus states**: 4px white outline with glow effect
- **TV-safe zones**: Content kept 5% away from screen edges
- **Simplified layouts**: Larger cards, horizontal carousels
- **Better contrast**: Optimized colors for TV displays

### Remote Control Navigation
- **D-pad support**: Arrow keys navigate between elements
- **Back button**: Samsung/LG back button closes modals and players
- **Enter/Select**: Activates focused elements
- **Spatial navigation**: Smart focus management

## Testing on Samsung TV

### Method 1: Samsung Internet Browser (Recommended)
1. On your Samsung TV, open the **Samsung Internet** browser app
2. Navigate to: `https://adajoon.com`
3. The site will automatically detect it's running on a TV
4. You'll see a "TV Mode" badge in the top-right corner
5. Use your remote control arrows to navigate

### Method 2: Development Testing
If you're developing locally:
1. Find your computer's local IP address
2. On Samsung TV browser, go to: `http://YOUR_IP:8000`
3. Make sure your firewall allows the connection

### Expected Behavior on Samsung TV
- ✅ Page loads and displays content
- ✅ "TV Mode" badge appears in top-right
- ✅ All text and buttons are larger
- ✅ Arrow keys navigate between elements
- ✅ Back button on remote closes modals/players
- ✅ Focus indicators (white outline) show current selection
- ✅ Video player controls are accessible via remote

## Browser Compatibility

### Build Configuration
The app is built with:
- **Target**: ES2015 (compatible with Samsung Tizen 2.4+)
- **CSS Target**: Chrome 61 (2017+)
- **Polyfills**: Included via Vite for older browsers

### Supported TV Platforms
- ✅ Samsung Tizen (2017+)
- ✅ LG webOS (2017+)
- ✅ Sony Bravia (Android TV)
- ✅ Any Smart TV with modern browser (Chrome 61+)

### Known Limitations
- OAuth (Google/Apple sign-in) may not work on some TVs - use guest mode
- WebAuthn (passkey) not supported on most TVs
- Some advanced JavaScript features may be polyfilled

## Troubleshooting

### Page Shows Nothing / Blank Screen
If the page doesn't load on Samsung TV:

1. **Check JavaScript Console** (if accessible):
   - Open Samsung TV developer tools (if available)
   - Look for JavaScript errors

2. **Clear Browser Cache**:
   - Go to Samsung Internet settings
   - Clear browsing data and cache
   - Reload the page

3. **Check Network Connection**:
   - Ensure TV is connected to internet
   - Test with other websites (e.g., google.com)

4. **Try Different URL**:
   - Try `http://adajoon.com` instead of `https://`
   - Some TVs have issues with HTTPS/CSP

5. **Disable Service Workers**:
   - Service workers are already disabled in our app
   - But old cached versions might interfere

### Remote Control Not Working
- Make sure the page has focus (click/press enter)
- Check if TV remote is in "pointer mode" - switch to D-pad mode
- Some remotes have a mode toggle button

### Content Cut Off at Edges
- This shouldn't happen (we have 5% safe zones)
- Check TV's picture settings - disable "overscan"
- Adjust TV display settings to "Just Scan" or "Screen Fit"

### Performance Issues
- TV browsers are slower than desktop
- Animations are reduced to 0.2s for TV
- Large video files may buffer more
- Try reducing video quality

## Development

### Testing TV Mode Locally

#### Simulate TV User Agent
Add this to your browser console:
```javascript
Object.defineProperty(navigator, 'userAgent', {
  get: () => 'Mozilla/5.0 (SMART-TV; Linux; Tizen 2.4.0) AppleWebKit/538.1'
});
location.reload();
```

#### Use Browser DevTools Device Emulation
1. Open Chrome DevTools (F12)
2. Enable device toolbar (Ctrl+Shift+M)
3. Edit user agent string to include "Tizen" or "TV"
4. Refresh page

### Key Files
- `frontend/src/utils/deviceDetection.js` - Device detection logic
- `frontend/src/hooks/useDevice.jsx` - Device context provider
- `frontend/src/hooks/useTVNavigation.js` - Remote control handling
- `frontend/src/styles/tv.css` - TV-specific styles
- `frontend/src/components/TVDebugInfo.jsx` - Debug indicator

### Adding TV-Specific Features

#### Detect TV Device in Component
```javascript
import { useDevice } from '../hooks/useDevice';

function MyComponent() {
  const { isTV, isTizen, isWebOS } = useDevice();
  
  if (isTV) {
    return <TVOptimizedView />;
  }
  return <DesktopView />;
}
```

#### Handle Remote Control Buttons
```javascript
import { useTVNavigation } from '../hooks/useTVNavigation';

function MyComponent() {
  useTVNavigation({
    enabled: true,
    onBack: () => console.log('Back button pressed'),
    onSelect: () => console.log('Enter button pressed'),
    onNavigate: (direction) => console.log('Arrow:', direction),
  });
}
```

#### TV-Only CSS
```css
/* Only apply on TV devices */
body.tv-device .my-element {
  font-size: 32px;
  padding: 20px;
}
```

## Deployment

### Environment Variables
No special environment variables needed for TV support.

### Build
```bash
cd frontend
npm run build
```

The build automatically includes:
- ES2015 compatibility
- CSS polyfills
- TV-specific styles bundled

### Railway Deployment
TV optimization works automatically on Railway:
1. Push changes to git
2. Railway auto-deploys
3. TV users access via `adajoon.com`
4. Desktop users see normal interface

## Future Enhancements

### Planned Features
- [ ] Voice search (via Samsung Bixby API)
- [ ] TV-specific shortcuts (colored buttons: red, green, yellow, blue)
- [ ] Picture-in-picture mode for TV
- [ ] TV-optimized video player with trick play
- [ ] Simplified authentication (TV code pairing)
- [ ] Chromecast integration
- [ ] Continue watching across devices

### Native App (Future)
For best performance, consider native TV apps:
- Samsung Tizen native app (Tizen Studio)
- LG webOS native app (webOS SDK)
- Android TV app (React Native for TV)
- Apple tvOS app (React Native for TV)

## Support

### Tested On
- ✅ Samsung Tizen 2.4+ (2017 models and newer)
- ✅ Desktop browsers (simulated TV mode)
- ⚠️ LG webOS (untested, should work)
- ⚠️ Android TV (untested, should work)

### Report Issues
If you encounter issues on your TV:
1. Note the TV model and year
2. Note the browser version (if available)
3. Describe what's not working
4. Include any error messages
5. Create an issue in the repository

## Resources

- [Samsung Tizen Web API](https://developer.samsung.com/smarttv/develop/api-references/tizen-web-device-api-references.html)
- [LG webOS Web API](https://webostv.developer.lge.com/api/web-api/)
- [W3C Spatial Navigation](https://www.w3.org/TR/css-nav-1/)
- [10-foot UI Guidelines](https://www.microsoft.com/design/inclusive/)

---

**Version**: 1.0.0  
**Last Updated**: April 5, 2026  
**Tested Platforms**: Samsung Tizen 2.4+, Desktop browsers
