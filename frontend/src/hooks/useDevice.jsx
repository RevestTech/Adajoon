import { createContext, useContext, useState, useEffect, useMemo } from "react";
import { getDeviceType, isTVDevice, getTVPlatform, getScreenSize, DEVICE_TYPES } from "../utils/deviceDetection";

const DeviceContext = createContext(null);

export function DeviceProvider({ children }) {
  const [deviceType, setDeviceType] = useState(() => getDeviceType());
  const [tvPlatform, setTvPlatform] = useState(() => getTVPlatform());
  const [screenSize, setScreenSize] = useState(() => getScreenSize());

  useEffect(() => {
    const handleResize = () => {
      setScreenSize(getScreenSize());
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const value = useMemo(() => ({
    deviceType,
    isTV: deviceType === DEVICE_TYPES.TV,
    isMobile: deviceType === DEVICE_TYPES.MOBILE,
    isTablet: deviceType === DEVICE_TYPES.TABLET,
    isDesktop: deviceType === DEVICE_TYPES.DESKTOP,
    tvPlatform,
    screenSize,
    isTizen: tvPlatform === 'tizen',
    isWebOS: tvPlatform === 'webos',
  }), [deviceType, tvPlatform, screenSize]);

  return (
    <DeviceContext.Provider value={value}>
      {children}
    </DeviceContext.Provider>
  );
}

export function useDevice() {
  const context = useContext(DeviceContext);
  if (!context) {
    throw new Error('useDevice must be used within DeviceProvider');
  }
  return context;
}
