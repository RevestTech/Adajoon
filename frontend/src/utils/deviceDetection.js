export const DEVICE_TYPES = {
  TV: 'tv',
  MOBILE: 'mobile',
  TABLET: 'tablet',
  DESKTOP: 'desktop',
};

export function getDeviceType() {
  if (typeof navigator === 'undefined') {
    return DEVICE_TYPES.DESKTOP;
  }

  const ua = navigator.userAgent;

  if (/TV|Tizen|webOS|SmartTV|BRAVIA|NetCast|NETTV|AppleTV|GoogleTV|HbbTV/i.test(ua)) {
    return DEVICE_TYPES.TV;
  }

  if (/iPad|Android(?!.*Mobile)/i.test(ua)) {
    return DEVICE_TYPES.TABLET;
  }

  if (/Mobile|Android|iPhone|iPod|BlackBerry|IEMobile|Opera Mini/i.test(ua)) {
    return DEVICE_TYPES.MOBILE;
  }

  return DEVICE_TYPES.DESKTOP;
}

export function isTVDevice() {
  return getDeviceType() === DEVICE_TYPES.TV;
}

export function isMobileDevice() {
  return getDeviceType() === DEVICE_TYPES.MOBILE;
}

export function isTabletDevice() {
  return getDeviceType() === DEVICE_TYPES.TABLET;
}

export function isDesktopDevice() {
  return getDeviceType() === DEVICE_TYPES.DESKTOP;
}

export function getTVPlatform() {
  if (!isTVDevice()) return null;

  const ua = navigator.userAgent;

  if (/Tizen/i.test(ua)) return 'tizen';
  if (/webOS/i.test(ua)) return 'webos';
  if (/BRAVIA/i.test(ua)) return 'bravia';
  if (/AppleTV/i.test(ua)) return 'appletv';
  if (/GoogleTV/i.test(ua)) return 'googletv';

  return 'unknown';
}

export function getScreenSize() {
  if (typeof window === 'undefined') {
    return { width: 1920, height: 1080 };
  }

  return {
    width: window.innerWidth || window.screen?.width || 1920,
    height: window.innerHeight || window.screen?.height || 1080,
  };
}

export function is4KScreen() {
  const { width, height } = getScreenSize();
  return width >= 3840 || height >= 2160;
}

export function supportsPointerEvents() {
  if (typeof window === 'undefined') return true;
  return window.PointerEvent !== undefined;
}

export function supportsTouchEvents() {
  if (typeof window === 'undefined') return false;
  return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
}
